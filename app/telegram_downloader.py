import os
import logging
from telegram import Video
from telegram.ext import ContextTypes
from config import Config

logger = logging.getLogger(__name__)


async def download_telegram_video(
    video: Video,
    context: ContextTypes.DEFAULT_TYPE,
    download_dir: str = None
) -> str:
    """
    Download a video from Telegram.
    
    Args:
        video: Telegram Video object
        context: Telegram context for bot operations
        download_dir: Directory to save the video (defaults to Config.DOWNLOAD_DIR)
    
    Returns:
        Path to the downloaded video file
    
    Raises:
        ValueError: If video exceeds size limit
        Exception: If download fails
    """
    # Check file size
    if video.file_size > Config.TELEGRAM_VIDEO_MAX_SIZE:
        raise ValueError(
            f"Video size ({video.file_size} bytes) exceeds maximum "
            f"({Config.TELEGRAM_VIDEO_MAX_SIZE} bytes)"
        )
    
    # Use configured download directory if not specified
    if download_dir is None:
        download_dir = Config.DOWNLOAD_DIR
    
    # Ensure download directory exists
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        # Get file from Telegram
        file = await video.get_file()
        
        # Generate filename (use file_unique_id to avoid collisions)
        # Format: telegram_video_{unique_id}.mp4
        filename = f"telegram_video_{video.file_unique_id}.mp4"
        filepath = os.path.join(download_dir, filename)
        
        logger.info(
            f"Downloading Telegram video: file_id={video.file_id}, "
            f"size={video.file_size}, path={filepath}"
        )
        
        # Download the file
        await file.download_to_drive(filepath)
        
        logger.info(f"Telegram video downloaded successfully: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error downloading Telegram video: {e}")
        raise


def get_video_info(video: Video) -> dict:
    """
    Extract useful information from a Telegram Video object.
    
    Args:
        video: Telegram Video object
    
    Returns:
        Dictionary with video information
    """
    return {
        'file_id': video.file_id,
        'file_unique_id': video.file_unique_id,
        'file_size': video.file_size,
        'duration': video.duration,
        'width': video.width,
        'height': video.height,
        'mime_type': video.mime_type,
    }
