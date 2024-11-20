import os
import aiohttp
import re
import logging
import time
from pyrogram.types import Message

PROGRESS_BAR_TEMPLATE = """
Percentage: {percentage}% | {current}/{total}
Speed: {speed}/s | ETA: {eta}
"""

def progressArgs(action: str, message: Message, start_time):
    return (
        action,
        message,
        start_time,
        PROGRESS_BAR_TEMPLATE,
        '▓',
        '░'
    )

async def async_download_file(url, filename, progress=None, progress_args=()):
    """
    Asynchronously download a file from a URL and save it locally.
    """
    download_directory = "downloads"
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    file_path = os.path.join(download_directory, filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception("Download failed.")

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(file_path, "wb") as file:
                async for chunk in response.content.iter_chunked(1024):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if progress:
                        await progress(downloaded_size, total_size, *progress_args)

    return file_path

async def get_file_size(url):
    """
    Fetch the file size from a URL.
    """
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            if response.status != 200:
                raise Exception("Failed to fetch file size.")
            return int(response.headers.get("content-length", 0))

async def get_filename(url):
    """
    Extract the file name from a URL or its headers.
    """
    async with aiohttp.ClientSession() as session:
        async with session.head(url) as response:
            if response.status != 200:
                raise Exception("Failed to fetch filename.")
            disposition = response.headers.get("content-disposition", "")
            match = re.findall(r'filename="(.+?)"', disposition)
            return match[0] if match else os.path.basename(url)

def file_size_format(size_in_bytes):
    """
    Format the file size into human-readable form.
    """
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_in_bytes >= 1024 and i < len(size_name) - 1:
        size_in_bytes /= 1024.0
        i += 1
    return f"{size_in_bytes:.2f} {size_name[i]}"

async def rename_file(downloaded_file, new_name):
    """
    Rename a downloaded file.
    """
    directory, _ = os.path.split(downloaded_file)
    ext = os.path.splitext(downloaded_file)[1]
    new_file_path = os.path.join(directory, f"{new_name}{ext}")
    os.rename(downloaded_file, new_file_path)
    return new_file_path

async def upload_file(client, chat_id, file_path, as_document=False):
    """
    Upload a file to the specified chat.
    """
    try:
        if as_document:
            await client.send_document(chat_id, document=file_path)
        else:
            await client.send_video(chat_id, video=file_path)
    except Exception as e:
        logging.error(f"Error during file upload: {e}")
        raise

async def convert_file(file_path, as_document=False):
    """
    Handle file conversion (document to video or vice versa).
    """
    if as_document:
        converted_path = file_path
    else:
        converted_path = file_path  # Mock conversion logic; adjust if actual conversion is needed.
    return converted_path

async def delete_file(file_path):
    """
    Safely delete a file from the system.
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        logging.warning(f"File not found: {file_path}")
    except Exception as e:
        logging.error(f"Error deleting file: {e}")

def estimate_time(start_time, current_size, total_size):
    """
    Estimate remaining time for a download or upload.
    """
    elapsed_time = time.time() - start_time
    speed = current_size / elapsed_time if elapsed_time > 0 else 0
    remaining_time = (total_size - current_size) / speed if speed > 0 else 0
    return time.strftime("%H:%M:%S", time.gmtime(remaining_time)), speed

async def progress(current, total, action, message, start_time, template, completed_symbol, pending_symbol):
    """
    Update the progress bar for file operations.
    """
    percentage = (current / total) * 100
    completed_length = int(percentage / 10)
    progress_bar = completed_symbol * completed_length + pending_symbol * (10 - completed_length)
    elapsed_time, speed = estimate_time(start_time, current, total)
    progress_text = template.format(
        percentage=round(percentage, 2),
        current=file_size_format(current),
        total=file_size_format(total),
        speed=file_size_format(speed),
        eta=elapsed_time
    )
    try:
        await message.edit_text(f"**{action} Progress**\n\n{progress_text}\n[{progress_bar}]")
    except Exception as e:
        logging.error(f"Error updating progress: {e}")
