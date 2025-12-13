import os
from typing import Optional

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
    
    # Download Configuration
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./downloads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "5000000000"))  # 5GB default
    
    # yt-dlp Configuration
    YT_DLP_FORMAT: str = os.getenv("YT_DLP_FORMAT", "best")
    YT_DLP_QUALITY: str = os.getenv("YT_DLP_QUALITY", "best")
    YT_DLP_AUDIO_ONLY: bool = os.getenv("YT_DLP_AUDIO_ONLY", "false").lower() == "true"
    YT_DLP_PLAYLIST: bool = os.getenv("YT_DLP_PLAYLIST", "false").lower() == "true"
    YT_DLP_OUTPUT_TEMPLATE: str = os.getenv("YT_DLP_OUTPUT_TEMPLATE", "%(title)s.%(ext)s")
    
    # Enhanced naming Configuration
    ENHANCED_NAMING: bool = os.getenv("ENHANCED_NAMING", "true").lower() == "true"
    PLAYLIST_FOLDER: bool = os.getenv("PLAYLIST_FOLDER", "true").lower() == "true"
    
    # Bot Configuration
    BOT_START_MESSAGE: str = os.getenv("BOT_START_MESSAGE", "Welcome to YouTube Downloader Bot!\n\nSend me a YouTube link and I'll download it for you.")
    BOT_ERROR_MESSAGE: str = os.getenv("BOT_ERROR_MESSAGE", "An error occurred while processing your request.")
    BOT_PROCESSING_MESSAGE: str = os.getenv("BOT_PROCESSING_MESSAGE", "Processing your request...")
    BOT_SUCCESS_MESSAGE: str = os.getenv("BOT_SUCCESS_MESSAGE", "Download succeeded")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate configuration values"""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "YOUR_BOT_TOKEN":
            raise ValueError("BOT_TOKEN must be set in environment variables")
        
        # Ensure download directory exists
        os.makedirs(cls.DOWNLOAD_DIR, exist_ok=True)

# Initialize config
config = Config()