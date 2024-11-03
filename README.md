<h1 align="center">URLUploader Telegram Bot</h1>

<p align="center">
  <a href="https://github.com/bisnuray/URLUploader/stargazers"><img src="https://img.shields.io/github/stars/bisnuray/URLUploader?color=blue&style=flat" alt="GitHub Repo stars"></a>
  <a href="https://github.com/bisnuray/URLUploader/issues"><img src="https://img.shields.io/github/issues/bisnuray/URLUploader" alt="GitHub issues"></a>
  <a href="https://github.com/bisnuray/URLUploader/pulls"><img src="https://img.shields.io/github/issues-pr/bisnuray/URLUploader" alt="GitHub pull requests"></a>
  <a href="https://github.com/bisnuray/URLUploader/graphs/contributors"><img src="https://img.shields.io/github/contributors/bisnuray/URLUploader?style=flat" alt="GitHub contributors"></a>
  <a href="https://github.com/bisnuray/URLUploader/network/members"><img src="https://img.shields.io/github/forks/bisnuray/URLUploader?style=flat" alt="GitHub forks"></a>
</p>

<p align="center">
  <em>URLUploader: An advanced Telegram bot script to download files from direct download URLs, check file sizes, rename files, and upload them with progress indicators directly to Telegram.</em>
</p>
<hr>

## ✨ Features

- 📥 Download files from direct download URLs and upload them to Telegram.
- 📊 Shows download and upload progress using custom handlers.
- ✏️ Rename Option: Allows renaming the file before uploading.

## Requirements

Before you begin, ensure you have met the following requirements:

- Python 3.8 or higher.
- `pyrofork`, `tgcrypto`, `pyleaves` and `aiohttp` libraries.
- A Telegram bot token (you can get one from [@BotFather](https://t.me/BotFather) on Telegram).
- API ID and Hash: You can get these by creating an application on [my.telegram.org](https://my.telegram.org).
- To Get `SESSION_STRING` Open [@SmartUtilBot](https://t.me/SmartUtilBot). Bot and use /pyro command and then follow all instructions.

## Installation

To install `pyrofork`, `tgcrypto`, `pyleaves` and `aiohttp` run the following command:

```bash
pip install pyrofork tgcrypto pyleaves aiohttp
```

**Note: If you previously installed `pyrogram`, uninstall it before installing `pyrofork`.**

## Configuration

1. Open the `config.py` file in your favorite text editor.
2. Replace the placeholders for `API_ID`, `API_HASH`, `SESSION_STRING`, and `BOT_TOKEN` with your actual values:
   - **`API_ID`**: Your API ID from [my.telegram.org](https://my.telegram.org).
   - **`API_HASH`**: Your API Hash from [my.telegram.org](https://my.telegram.org).
   - **`SESSION_STRING`**: The session string generated using [@SmartUtilBot](https://t.me/SmartUtilBot).
   - **`BOT_TOKEN`**: The token you obtained from [@BotFather](https://t.me/BotFather).

## Deploy the Bot

```sh
git clone https://github.com/bisnuray/URLUploader
cd URLUploader
python uploder.py
```

## Usage

Send a URL to the bot in a private message. If the file is valid and within the size limit, the bot will present two options:

- **Default:** Download and upload the file with its original name.
- **Rename:** Allows you to specify a new filename before upload.
- **Download Progress:** While downloading and uploading, progress messages display current status.

✨ **Note**: If you found this repo helpful, please fork and star it. Also, feel free to share with proper credit!

## Author

- Name: Bisnu Ray
- Telegram: [@itsSmartDev](https://t.me/itsSmartDev)

Feel free to reach out if you have any questions or feedback.
