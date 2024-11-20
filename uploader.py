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
pending_downloads = {}

URL_REGEX = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


# Start Command Handler
@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    await message.reply_text(
        text=(
            "**Welcome to File Uploader Bot!** 🎉\n\n"
            "This bot helps you download and upload files from any direct URL. "
            "You can also rename files before uploading.\n\n"
            "Just send me a link, and I'll handle the rest!\n\n"
            "**Commands:**\n"
            "• `/help` - Get detailed instructions\n\n"
            "Happy Uploading! 😊"
        ),
        disable_web_page_preview=True
    )


# Help Command Handler
@bot.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    await message.reply_text(
        text=(
            "**Help Menu** 📖\n\n"
            "Here’s how to use this bot:\n\n"
            "1️⃣ **Send a URL**: Send me a direct link to a file. I'll fetch and upload it.\n"
            "2️⃣ **Choose an Option**: After processing the link, you can:\n"
            "   • Upload with the default name\n"
            "   • Rename the file before uploading\n\n"
            "🎯 **Commands:**\n"
            "• `/start` - Restart the bot\n"
            "• `/help` - Display this help message\n\n"
            "Let’s get started!"
        ),
        disable_web_page_preview=True
    )


# Message Handler for Links
@bot.on_message(filters.text & filters.private)
async def handle_message(client, message: Message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in pending_renames:
        new_name = text

        if not new_name:
            await message.reply_text("**Invalid filename. Please provide a valid name.**")
            return

        url = pending_renames.pop(chat_id)
        base_name, ext = os.path.splitext(url.split('/')[-1].split('?')[0])
        new_name_with_ext = f"{new_name}{ext}"

        try:
            start_time = time.time()
            editable_text = await client.send_message(chat_id, "📥 Downloading...")

            downloaded_file = await async_download_file(
                url,
                new_name_with_ext,
                progress=Leaves.progress_for_pyrogram,
                progress_args=progressArgs("📥 Downloading Progress", editable_text, start_time)
            )

            upload_start_time = time.time()
            await message.reply_document(
                document=downloaded_file,
                file_name=new_name_with_ext,
                progress=Leaves.progress_for_pyrogram,
                progress_args=progressArgs("📤 Uploading Progress", editable_text, upload_start_time)
            )

            await editable_text.delete()
            os.remove(downloaded_file)
            await message.reply_text("✅ **Upload Completed!**")

        except Exception as e:
            await editable_text.delete()
            await message.reply_text(f"❌ **Error:** {str(e)}")

    elif re.match(URL_REGEX, text):
        url = text
        processing_message = await message.reply_text("🔄 **Processing, please wait...**")
        try:
            file_size_bytes = await get_file_size(url)
            if file_size_bytes == 0:
                await processing_message.edit_text("❌ **File information is not available for this link.**")
                return

            formatted_size = file_size_format(file_size_bytes)
            filename = await get_filename(url)
            unique_id = str(uuid.uuid4())
            pending_downloads[unique_id] = {"url": url, "filename": filename}

            file_info = f"**📄 File Name:** `{filename}`\n**📦 File Size:** `{formatted_size}`"

            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 Default", callback_data=f"default|{unique_id}"),
                 InlineKeyboardButton("✏️ Rename", callback_data=f"rename|{unique_id}")]
            ])

            await processing_message.edit_text(
                text=f"**How would you like to proceed?**\n\n{file_info}",
                reply_markup=reply_markup
            )

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            await processing_message.edit_text(f"❌ **Error:** {str(e)}")


# Callback Query Handler
@bot.on_callback_query(filters.regex(r"^(default|rename)\|"))
async def on_file_decision(client, callback_query):
    action, unique_id = callback_query.data.split("|")
    chat_id = callback_query.message.chat.id

    download_info = pending_downloads.get(unique_id)
    if not download_info:
        await callback_query.message.edit_text("❌ **An error occurred: Invalid action.**")
        return

    url = download_info["url"]
    filename = download_info["filename"]

    try:
        file_size_bytes = await get_file_size(url)

        if file_size_bytes > MAX_FILE_SIZE:
            await callback_query.message.edit_text("❌ **The file size exceeds the 2GB limit.**")
            return

        if action == "default":
            start_time = time.time()
            editable_text = await client.send_message(chat_id, "⏳ **Processing your request...**")

            downloaded_file = await async_download_file(
                url,
                filename,
                progress=Leaves.progress_for_pyrogram,
                progress_args=progressArgs("📥 Downloading Progress", editable_text, start_time)
            )

            upload_start_time = time.time()
            await callback_query.message.reply_document(
                document=downloaded_file,
                file_name=filename,
                progress=Leaves.progress_for_pyrogram,
                progress_args=progressArgs("📤 Uploading Progress", editable_text, upload_start_time)
            )

            await editable_text.delete()
            os.remove(downloaded_file)
            await callback_query.message.reply_text("✅ **Upload Completed!**")

        elif action == "rename":
            pending_renames[chat_id] = url
            await callback_query.message.edit_text("✏️ **Send the new name for the file:**")

    except Exception as e:
        await callback_query.message.edit_text(f"❌ **Error:** {str(e)}")


# Flask app for the keep-alive feature
app = Flask(__name__)

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

# Start the bot and the keep-alive server
if __name__ == "__main__":
    keep_alive()  # Start the keep-alive Flask server
    user.start()
    bot.run()
