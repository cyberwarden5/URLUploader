import os
import re
import uuid
import time
import logging
import asyncio
import aiohttp
from flask import Flask
from threading import Thread
from pyleaves import Leaves
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from helpers.utils import (
    async_download_file,
    get_file_size,
    file_size_format,
    get_filename,
    progressArgs
)

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    SESSION_STRING,
    MAX_FILE_SIZE
)

bot = Client(
    "uploader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    parse_mode=ParseMode.MARKDOWN
)

user = Client(
    "user_session",
    workers=1000,
    session_string=SESSION_STRING
)

pending_renames = {}
pending_conversions = {}
pending_downloads = {}

URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text(
        "Hello! 👋\n\nI'm here to help you manage files. Send a file or URL, and I'll assist with downloading, renaming, or converting it.\n\nType /help for more options."
    )

@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    await message.reply_text(
        "**Help Menu**\n\n"
        "• **Send a URL or file**: I will assist with renaming, downloading, or converting.\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
    )

@bot.on_message(filters.text & filters.private)
async def handle_text(client, message: Message):
    text = message.text.strip()
    chat_id = message.chat.id

    if re.match(URL_REGEX, text):
        url = text
        try:
            file_size_bytes = await get_file_size(url)
            if file_size_bytes == 0:
                await message.reply_text("**File information is not available for this link.**")
                return

            formatted_size = file_size_format(file_size_bytes)
            filename = await get_filename(url)
            unique_id = str(uuid.uuid4())
            pending_downloads[unique_id] = {"url": url, "filename": filename}

            file_info = f"**Name**: `{filename}`\n**Size**: `{formatted_size}`"
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("Default", callback_data=f"default|{unique_id}"),
                 InlineKeyboardButton("Rename", callback_data=f"rename_url|{unique_id}")]
            ])

            await message.reply_text(
                text=f"**📤 How would you like to upload?**\n\n{file_info}",
                reply_markup=buttons
            )
        except Exception as e:
            logging.error(f"Error fetching URL: {str(e)}")
            await message.reply_text(f"**Error: {str(e)}**")
    elif chat_id in pending_renames:
        await handle_rename(client, message)

@bot.on_message(filters.video | filters.document & filters.private)
async def handle_file(client, message: Message):
    chat_id = message.chat.id
    file = message.video or message.document
    file_name = file.file_name
    file_size = file_size_format(file.file_size)
    file_id = file.file_id

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Rename", callback_data=f"rename_file|{file_id}"),
         InlineKeyboardButton("Convert to Document" if file.mime_type.startswith("video/") else "Convert to Video", callback_data=f"convert_file|{file_id}")]
    ])

    await message.reply_text(
        f"**What do you want to do with this file?**\n\n**Name**: `{file_name}`\n**Size**: `{file_size}`",
        reply_markup=buttons
    )

@bot.on_callback_query(filters.regex(r"^(default|rename_url|rename_file|convert_file)\|"))
async def on_option(client, callback_query):
    action, unique_id = callback_query.data.split("|")
    chat_id = callback_query.message.chat.id

    if action == "default":
        await handle_url_download(client, callback_query, unique_id)
    elif action == "rename_url":
        pending_renames[chat_id] = unique_id
        await callback_query.message.edit_text("**Send the new name for the file.**")
    elif action == "rename_file":
        pending_renames[chat_id] = unique_id
        await callback_query.message.edit_text("**Send the new name for the file.**")
    elif action == "convert_file":
        await process_conversion(client, chat_id, unique_id, callback_query)

async def handle_rename(client, message: Message):
    chat_id = message.chat.id
    new_name = message.text.strip()

    if chat_id in pending_renames:
        file_id = pending_renames.pop(chat_id)
        file = await client.get_messages(chat_id, file_ids=file_id)
        file_name, ext = os.path.splitext(file.video.file_name or file.document.file_name)
        new_file_name = f"{new_name}{ext}"

        try:
            start_time = time.time()
            editable_text = await client.send_message(chat_id, "📥 Downloading...")

            downloaded_file = await client.download_media(file, file_name=new_file_name)

            await editable_text.edit_text("📤 Uploading...")
            await client.send_document(chat_id, document=downloaded_file, file_name=new_file_name)
            os.remove(downloaded_file)

        except Exception as e:
            logging.error(f"Error during rename: {str(e)}")
            await message.reply_text(f"**Error: {str(e)}**")

async def handle_url_download(client, callback_query, unique_id):
    download_info = pending_downloads.get(unique_id)
    if not download_info:
        await callback_query.message.edit_text("**Invalid action.**")
        return

    url = download_info["url"]
    filename = download_info["filename"]

    try:
        start_time = time.time()
        editable_text = await client.send_message(callback_query.message.chat.id, "📥 Downloading...")

        downloaded_file = await async_download_file(url, filename)
        await editable_text.edit_text("📤 Uploading...")

        await client.send_document(callback_query.message.chat.id, document=downloaded_file, file_name=filename)
        os.remove(downloaded_file)

    except Exception as e:
        logging.error(f"Error during URL download: {str(e)}")
        await callback_query.message.edit_text(f"**Error: {str(e)}**")

async def process_conversion(client, chat_id, file_id, callback_query):
    file = await client.get_messages(chat_id, file_ids=file_id)
    try:
        start_time = time.time()
        editable_text = await client.send_message(chat_id, "📥 Downloading...")
        downloaded_file = await client.download_media(file)

        await editable_text.edit_text("📤 Uploading...")

        if file.mime_type.startswith("video/"):
            await client.send_document(chat_id, document=downloaded_file)
        else:
            await client.send_video(chat_id, video=downloaded_file)

        os.remove(downloaded_file)
        await callback_query.message.delete()

    except Exception as e:
        logging.error(f"Error during conversion: {str(e)}")
        await callback_query.message.edit_text(f"**Error: {str(e)}**")

app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

if __name__ == "__main__":
    keep_alive()
    user.start()
    bot.run()
