import os
import logging
import re
from typing import Dict, Any, Optional
from config import Config
import yt_dlp

logger = logging.getLogger(__name__)

def get_yt_dlp_options(progress_hook=None) -> Dict[str, Any]:
    """Generate yt-dlp options based on configuration"""
    
    # Basic options
    ydl_opts = {
        'format': Config.YT_DLP_FORMAT,
        'outtmpl': Config.YT_DLP_OUTPUT_TEMPLATE,
        'paths': {
            'home': Config.DOWNLOAD_DIR,
            'temp': Config.TEMP_DOWNLOAD_DIR
        },
        'noplaylist': not Config.YT_DLP_PLAYLIST,
        'progress_hooks': [progress_hook] if progress_hook else [],
        'max_filesize': Config.MAX_FILE_SIZE if Config.MAX_FILE_SIZE > 0 else None,
        'concurrent_fragment_downloads': Config.CONCURRENT_FRAGMENT_DOWNLOADS,
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

def sanitize_filename(filename: str, is_playlist=False) -> str:
    """Remove invalid characters from filename and apply media server compatible formatting"""
    # Replace problematic characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # For media server compatibility, remove or replace additional characters
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Limit length to prevent issues with filesystems (e.g., 255 chars max)
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    # If empty after sanitization, use a default name
    if not sanitized:
        sanitized = "video"
    
    # For playlist items, we might want to include additional info
    if is_playlist:
        # Remove any remaining problematic characters that could cause issues
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    return sanitized

def get_video_info(url: str) -> Optional[Dict[str, Any]]:
    """
    Get video or playlist information without downloading.
    
    Args:
        url: YouTube URL
    
    Returns:
        Dictionary with video/playlist info or None if failed
    """
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just get metadata
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info:
                # Check if it's a playlist
                is_playlist = 'entries' in info
                
                if is_playlist:
                    return {
                        'type': 'playlist',
                        'title': info.get('title', 'Unknown Playlist'),
                        'video_count': len(info.get('entries', [])),
                        'uploader': info.get('uploader', 'Unknown'),
                    }
                else:
                    return {
                        'type': 'video',
                        'title': info.get('title', 'Unknown Video'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                    }
    except Exception as e:
        logger.error(f"Error getting video info for {url}: {e}")
        return None


def download_video(url: str, progress_hook=None) -> None:
    """
    Download video or playlist from the given URL.
    Uses yt-dlp's native playlist handling via output template.
    
    Args:
        url: YouTube URL to download
        progress_hook: Optional callback function for progress updates
    """
    try:
        download_opts = get_yt_dlp_options(progress_hook=progress_hook)
        
        # Override output template to handle playlists automatically
        if Config.PLAYLIST_FOLDER:
            # Use yt-dlp's built-in playlist_title field with fallback to current dir
            # This automatically creates playlist directories when needed
            template = os.path.join(
                "%(playlist_title|.)s",  # Use playlist title or "." for single videos
                Config.YT_DLP_OUTPUT_TEMPLATE
            )
            download_opts['outtmpl'] = template
            logger.info(f"Using playlist-aware template: {template}")
        
        # Perform the download
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download([url])
            
    except Exception as e:
        logger.error(f"Error downloading URL {url}: {e}")
        raise