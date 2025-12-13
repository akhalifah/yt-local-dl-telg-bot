import os
import logging
from typing import Dict, Any
from config import Config

logger = logging.getLogger(__name__)

def get_yt_dlp_options() -> Dict[str, Any]:
    """Generate yt-dlp options based on configuration"""
    
    # Basic options
    ydl_opts = {
        'format': Config.YT_DLP_FORMAT,
        'outtmpl': os.path.join(Config.DOWNLOAD_DIR, Config.YT_DLP_OUTPUT_TEMPLATE),
        'noplaylist': not Config.YT_DLP_PLAYLIST,
        'progress_hooks': [],
        'max_filesize': Config.MAX_FILE_SIZE if Config.MAX_FILE_SIZE > 0 else None,
    }
    
    # Audio-only option
    if Config.YT_DLP_AUDIO_ONLY:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }]
    
    # Additional options based on quality
    if Config.YT_DLP_QUALITY != "best":
        ydl_opts['format'] = f"{Config.YT_DLP_QUALITY}+bestaudio/best"
    
    return ydl_opts

def is_valid_youtube_url(url: str) -> bool:
    """Check if URL is a valid YouTube URL"""
    return "youtube.com" in url or "youtu.be" in url

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    import re
    return re.sub(r'[<>:"/\\|?*]', '_', filename)