import os
import re
import aiohttp
import math
import time

# Updated progress bar template
PROGRESS_BAR_TEMPLATE = """
**{action}**  
[{bar}] **{percentage:.2f}%**  
📦 **Done:** {current} / {total}  
⚡️ **Speed:** {speed}/s  
⏳ **ETA:** {est_time}
"""

def progressArgs(action: str, progress_message, start_time):
    return (
        action,
        progress_message,
        start_time,
        PROGRESS_BAR_TEMPLATE,
        '▰',  # Filled block
        '▱'   # Empty block
    )


async def async_download_file(url, filename, progress=None, progress_args=()):
    download_directory = "Download"
    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    file_path = os.path.join(download_directory, filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise Exception("Download failed with status code " + str(response.status))

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(file_path, "wb") as file:
                start_time = time.time()
                async for chunk in response.content.iter_chunked(1024):
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if progress:
                        await progress(
                            downloaded_size,
                            total_size,
                            *progress_args  # Ensure all progress_args are passed here
                        )

    return file_path


async def get_file_size(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=True) as response:
            size = response.headers.get('content-length')
            if size:
                return int(size)
            else:
                return 0


def file_size_format(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"


async def get_filename(url):
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=True) as response:
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                match = re.findall('filename="(.+)"', content_disposition)
                if match:
                    return match[0]
            return url.split('/')[-1].split('?')[0]


# Updated progress function
async def progress_for_pyrogram(current, total, action, progress_message, start_time, template, filled, empty):
    now = time.time()
    elapsed_time = now - start_time

    percentage = current * 100 / total
    speed = current / elapsed_time
    eta = (total - current) / speed if speed > 0 else 0

    bar_length = 20  # Length of the progress bar
    filled_length = math.floor(bar_length * current / total)
    bar = filled * filled_length + empty * (bar_length - filled_length)

    progress_text = template.format(
        action=action,
        bar=bar,
        percentage=percentage,
        current=file_size_format(current),
        total=file_size_format(total),
        speed=file_size_format(speed),
        est_time=time.strftime("%H:%M:%S", time.gmtime(eta))
    )

    try:
        await progress_message.edit_text(progress_text)
    except Exception as e:
        pass  # Ignore edit issues to keep bot running smoothly

