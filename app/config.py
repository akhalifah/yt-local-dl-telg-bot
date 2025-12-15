import os
from typing import Optional

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    
    # Download Configuration
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "5000000000"))  # 5GB default
    TEMP_DOWNLOAD_DIR: str = os.getenv("TEMP_DOWNLOAD_DIR", os.path.join(DOWNLOAD_DIR, "tmp"))
    
    # yt-dlp Configuration
    YT_DLP_FORMAT: str = os.getenv("YT_DLP_FORMAT", "best")
    YT_DLP_QUALITY: str = os.getenv("YT_DLP_QUALITY", "best")
    YT_DLP_AUDIO_ONLY: bool = os.getenv("YT_DLP_AUDIO_ONLY", "false").lower() == "true"
    YT_DLP_PLAYLIST: bool = os.getenv("YT_DLP_PLAYLIST", "false").lower() == "true"
    YT_DLP_OUTPUT_TEMPLATE: str = os.getenv("YT_DLP_OUTPUT_TEMPLATE", "%(title)s.%(ext)s")
    
    # Concurrency Configuration
    MAX_CONCURRENT_DOWNLOADS: int = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))
    CONCURRENT_FRAGMENT_DOWNLOADS: int = int(os.getenv("CONCURRENT_FRAGMENT_DOWNLOADS", "4"))
    
    # Progress Notification Configuration
    ENABLE_PROGRESS_NOTIFICATIONS: bool = os.getenv("ENABLE_PROGRESS_NOTIFICATIONS", "true").lower() == "true"
    PROGRESS_UPDATE_INTERVAL: int = int(os.getenv("PROGRESS_UPDATE_INTERVAL", "5"))  # Logs progress to console
    
    # Telegram Video Download Configuration
    AUTO_DOWNLOAD_TELEGRAM_VIDEOS: bool = os.getenv("AUTO_DOWNLOAD_TELEGRAM_VIDEOS", "true").lower() == "true"
    TELEGRAM_VIDEO_MAX_SIZE: int = int(os.getenv("TELEGRAM_VIDEO_MAX_SIZE", "20971520"))  # 20MB default
    
    # Enhanced naming Configuration
    ENHANCED_NAMING: bool = os.getenv("ENHANCED_NAMING", "true").lower() == "true"
    PLAYLIST_FOLDER: bool = os.getenv("PLAYLIST_FOLDER", "true").lower() == "true"
    
    # Bot Configuration
    BOT_START_MESSAGE: str = os.getenv("BOT_START_MESSAGE", "Welcome to YouTube Downloader Bot!\n\nSend me a YouTube link or video and I'll download it for you.")
    BOT_ERROR_MESSAGE: str = os.getenv("BOT_ERROR_MESSAGE", "An error occurred while processing your request.")
    BOT_PROCESSING_MESSAGE: str = os.getenv("BOT_PROCESSING_MESSAGE", "Processing your request...")
    BOT_SUCCESS_MESSAGE: str = os.getenv("BOT_SUCCESS_MESSAGE", "Download succeeded")
    BOT_QUEUE_MESSAGE: str = os.getenv("BOT_QUEUE_MESSAGE", "Your download is queued. Position: {position}/{total}")
    BOT_DOWNLOAD_START_MESSAGE: str = os.getenv("BOT_DOWNLOAD_START_MESSAGE", "Starting download... ({active}/{max} active)")
    BOT_PROGRESS_MESSAGE: str = os.getenv("BOT_PROGRESS_MESSAGE", "📥 Downloading: {percent}% | Speed: {speed} | ETA: {eta}")
    BOT_DOWNLOAD_COMPLETE_MESSAGE: str = os.getenv("BOT_DOWNLOAD_COMPLETE_MESSAGE", "✅ Download complete!")
    BOT_TELEGRAM_VIDEO_TOO_LARGE: str = os.getenv("BOT_TELEGRAM_VIDEO_TOO_LARGE", "❌ Video is too large (max 20MB for Telegram videos)")
    
    # Auth Messages
    BOT_AUTH_RESTRICTED: str = os.getenv("BOT_AUTH_RESTRICTED", "⛔ Access restricted.\nPlease authenticate using: `/auth <password>`")
    BOT_AUTH_REQUIRED_START: str = os.getenv("BOT_AUTH_REQUIRED_START", "🔒 **Authentication Required**\nThis bot is restricted to authorized users.\nPlease authenticate to use it: `/auth <password>`")
    BOT_AUTH_NOT_ENABLED: str = os.getenv("BOT_AUTH_NOT_ENABLED", "🔓 Authentication is not enabled.")
    BOT_AUTH_ALREADY_Authorized: str = os.getenv("BOT_AUTH_ALREADY_AUTHORIZED", "✅ You are already authorized.")
    BOT_AUTH_USAGE: str = os.getenv("BOT_AUTH_USAGE", "Usage: `/auth <password>`")
    BOT_AUTH_SUCCESS: str = os.getenv("BOT_AUTH_SUCCESS", "✅ Access granted! You can now use the bot.")
    BOT_AUTH_FAILED: str = os.getenv("BOT_AUTH_FAILED", "❌ Invalid password.")
    
    # Access Control Configuration
    BOT_ACCESS_PASSWORD: Optional[str] = os.getenv("BOT_ACCESS_PASSWORD")
    ALLOWED_USERS_FILE: str = os.getenv("ALLOWED_USERS_FILE", "allowed_users.json")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "./logs")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    
    @classmethod
    def validate(cls):
        """Validate configuration values"""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "YOUR_BOT_TOKEN":
            raise ValueError("BOT_TOKEN must be set in environment variables")
        
        # Ensure download directory exists
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DOWNLOAD_DIR, exist_ok=True)
        
        # Ensure log directory exists
        os.makedirs(cls.LOG_DIR, exist_ok=True)

# Initialize config
config = Config()