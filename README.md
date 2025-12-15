# YouTube Downloader Telegram Bot

A robust and efficient Telegram bot designed to download videos from YouTube and Telegram. Built with Python, it leverages `yt-dlp` for high-quality YouTube downloads and features a sophisticated concurrent download manager with a queuing system.

## 🚀 Overview

This bot provides a seamless interface for users to download content. Whether it's a single YouTube video, a full playlist, or a video file sent directly through Telegram, this bot handles it with ease. It is built to be deployed using Docker for easy scalability and management.

## ✨ Features

- **YouTube Downloads**:
  - High-quality video downloads using `yt-dlp`.
  - **Playlist Support**: Automatically detects playlists and saves them into dedicated subdirectories.
  - Smart metadata extraction (titles, thumbnails).

- **Telegram Downloads**:
  - Automatically downloads videos sent to the bot (configurable).
  - Handles large files (within Telegram Bot API limits).

- **Advanced Download Management**:
  - **Concurrency**: Supports multiple simultaneous downloads (configurable limit).
  - **Queue System**: Automatically queues requests when the active download limit is reached.
  - **Temp Directory Isolation**: Downloads are saved to a temporary folder while in progress and moved to the final directory only upon successful completion.

- **User Experience**:
  - **Real-time Status**: Commands to check the current queue status.
  - **Notifications**: Updates on download start and completion.
  - **Silent Operation**: Progress updates are logged to the console to keep the chat clean.

- **Configuration**:
  - Fully configurable via environment variables (`.env` file).
  - Customizable download paths, limits, and logging.

## 🛠 Usage

### Prerequisites
- Docker and Docker Compose installed.
- A Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather)).

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository_url>
   cd youtube-downloader-bot
   ```

2. **Configure Environment:**
   Create a `.env` file in the root directory (features usually pre-configured in `docker-compose.yml` or provided `.env` example):
   ```env
   BOT_TOKEN=your_telegram_bot_token_here
   DOWNLOAD_DIR=/app/downloads
   TEMP_DOWNLOAD_DIR=/app/temp_downloads
   MAX_CONCURRENT_DOWNLOADS=3
   MAX_CONCURRENT_DOWNLOADS=3
   LOG_LEVEL=INFO
   # Authentication (Optional)
   BOT_ACCESS_PASSWORD=your_secret_password
   ALLOWED_USERS_FILE=allowed_users.json
   ```

3. **Run with Docker Compose:**
   ```bash
   docker-compose up -d --build
   ```

### Bot Commands

- `/start`: Initialize the bot and receive a welcome message.
- `/queue`: View the status of the current download queue (active downloads, waiting tasks).

### How to Download

1. **YouTube**: Simply paste a valid YouTube link (video or playlist) into the chat. The bot will automatically add it to the queue.
2. **Telegram**: Forward or upload a video file to the chat. The bot will download it if `AUTO_DOWNLOAD_TELEGRAM_VIDEOS` is enabled.

## 🔐 Authentication

To restrict bot access to specific users, you can enable Pre-Shared Key (PSK) authentication.

### How it Works
1.  **Enable**: Set `BOT_ACCESS_PASSWORD` in your `.env` file.
2.  **Authenticate**: Unknown users must send `/auth <your_password>` to the bot once.
3.  **Persist**: The bot saves authorized user IDs to `allowed_users.json`. Authentication persists across restarts.

If `BOT_ACCESS_PASSWORD` is not set, the bot is public and anyone can use it.

### Commands
- `/start`: Initialize the bot.
- `/queue`: View status of current downloads.
- `/auth <password>`: Authenticate with the bot (if enabled).

## 🏗 Full Design

The application is structured to ensure responsiveness and stability, even under load.

### Core Components

1. **Bot Interface (`app/bot.py`)**:
   - Built with `python-telegram-bot` (async/await).
   - Handles incoming updates (messages, commands).
   - Validates inputs (YouTube URLs, file sizes).
   - Dispatches tasks to the Download Manager.

2. **Download Manager (`app/download_manager.py`)**:
   - **Singleton Pattern**: Ensures a single centralized manager handling all tasks.
   - **Concurrency Control**: Uses `asyncio.Semaphore` to limit the number of active downloads defined by `MAX_CONCURRENT_DOWNLOADS`.
   - **Thread Pool**: Offloads blocking I/O operations (like `yt-dlp` execution) to a `ThreadPoolExecutor` to prevent freezing the asyncio event loop.
   - **Queue Tracking**: Maintains counters for active, waiting, and total tasks to provide status updates.

3. **Configuration (`app/config.py`)**:
   - Centralized configuration class loading settings from environment variables.
   - Includes validation logic to ensure critical settings (like `BOT_TOKEN`) are present.

4. **Utilities (`app/utils.py`, `app/telegram_downloader.py`)**:
   - Wrappers for `yt-dlp` CLI interactions.
   - Logic for file system operations (moving files from temp to final destination).
   - Formatting and validation helpers.

### Data Flow

1. User sends a link.
2. `bot.py` validates the link and calls `download_manager.download()`.
3. `DownloadManager` creates a `DownloadTask` and acquires a semaphore.
   - If semaphore is available: The task starts immediately in a separate thread.
   - If semaphore is locked: The task waits in the asyncio queue.
4. `yt-dlp` downloads the file to `TEMP_DOWNLOAD_DIR`.
5. Upon completion, the file is moved to `DOWNLOAD_DIR`.
6. Use is notified of success/failure.

## ⚠️ Considerations

- **Blocking vs. Async**: Great care was taken to ensure that long-running download processes do not block the main bot loop. This is achieved by running `yt-dlp` in a separate thread pool while keeping the bot responsive.
- **File System Limits**: Ensure the host machine has sufficient disk space mounted to the Docker container's download volumes.
- **Telegram API Limits**: Telegram imposes limits on file sizes for bots (uploading 50MB, downloading 20MB without a local API server). This bot is configured to respect these limits or handle local downloads appropriately.
- **YouTube Rate Limiting**: Heavy usage might trigger YouTube's rate limiting. `yt-dlp` handles some of this, but it's a factor to keep in mind for high-traffic instances.

## 🤝 Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## 📄 License

[MIT License](LICENSE)