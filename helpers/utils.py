import os
import re
import logging
import aiohttp
from time import time

# Customizable progress bar template
PROGRESS_BAR_TEMPLATE = """
Action: {action}
Progress: {percentage}% [{current}/{total}]
Speed: {speed}/s | ETA: {est_time}
"""

def progressArgs(action: str, progress_message, start_time):
    """
    Provides arguments for progress display.
    
    Args:
        action (str): Description of the action being performed.
        progress_message: Message object for updating progress.
        start_time: Start time of the download or upload.

    Returns:
        tuple: Arguments required by the progress function.
    """
    return (
        action,
        progress_message,
        start_time,
        PROGRESS_BAR_TEMPLATE,
        '▓',  # Progress block symbol for completed portion
        '░'   # Symbol for remaining portion
    )

async def async_download_file(url, filename, progress=None, progress_args=()):
    """
    Asynchronously downloads a file from a URL and saves it locally.
    
    Args:
        url (str): File URL.
        filename (str): Name to save the downloaded file as.
        progress (function, optional): Callback function for tracking progress.
        progress_args (tuple, optional): Arguments for the progress callback.
    
    Returns:
        str: Path to the downloaded file.
    
    Raises:
        Exception: If the download fails.
    """
    download_directory = "Download"
    os.makedirs(download_directory, exist_ok=True)
    
    file_path = os.path.join(download_directory, filename)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception("Download failed with status code {}".format(response.status))
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, "wb") as file:
                start_time = time()
                async for chunk in response.content.iter_chunked(1024):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Progress callback update
                    if progress:
                        await progress(downloaded_size, total_size, *progress_args)
    
    return file_path

def file_size_format(num, suffix='B'):
    """
    Formats file size into a human-readable string.
    
    Args:
        num (int): File size in bytes.
        suffix (str): Suffix for size units.

    Returns:
        str: Formatted file size.
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

async def get_file_size(url):
    """
    Retrieves the file size from the headers of a URL.
    
    Args:
        url (str): File URL.

    Returns:
        int: File size in bytes, or 0 if unavailable.
    """
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=True) as response:
            size = response.headers.get('content-length')
            return int(size) if size else 0

async def get_filename(url):
    """
    Extracts filename from the URL or content-disposition headers.

    Args:
        url (str): File URL.

    Returns:
        str: Filename for saving the downloaded file.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True) as response:
                # Attempt to retrieve filename from Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    filename_match = re.findall(r'filename="(.+)"', content_disposition)
                    if filename_match:
                        return filename_match[0]

                # Fallback to extracting filename from URL
                return url.split('/')[-1].split('?')[0]
    except Exception as e:
        logging.error(f"Error fetching filename from headers: {str(e)}")
        # Fallback to extracting filename from URL on exception
        return url.split('/')[-1].split('?')[0]
