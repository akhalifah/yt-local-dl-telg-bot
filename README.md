# YouTube Downloader Telegram Bot

A Telegram bot that downloads YouTube videos using yt-dlp.

## Features

- Download YouTube videos in various formats
- Support for audio-only downloads
- Playlist support (optional)
- Configurable download paths
- File size limits
- Error handling and logging

## Setup

### 1. Get Telegram Bot Token

1. Talk to [@BotFather](https://t.me/BotFather) on Telegram
2. Use `/newbot` command to create a new bot
3. Copy the token provided

### 2. Configuration

Create a `.env` file with your configuration:

```bash
BOT_TOKEN=your_telegram_bot_token_here
DOWNLOAD_DIR=./downloads
MAX_FILE_SIZE=5000000000
YT_DLP_FORMAT=best
YT_DLP_QUALITY=best
YT_DLP_AUDIO_ONLY=false
YT_DLP_PLAYLIST=false
YT_DLP_OUTPUT_TEMPLATE=%(title)s.%(ext)s
LOG_LEVEL=INFO