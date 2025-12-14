import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DownloadTask:
    """Represents a download task in the queue"""
    url: str
    user_id: int
    chat_id: int
    task_type: str  # 'youtube' or 'telegram'
    queued_at: datetime
    task_id: int


class DownloadManager:
    """
    Manages concurrent downloads with configurable limits.
    Uses asyncio.Semaphore to limit concurrent downloads and ThreadPoolExecutor
    to run blocking yt-dlp calls without blocking the event loop.
    """
    
    def __init__(self, max_concurrent: int):
        """
        Initialize the download manager.
        
        Args:
            max_concurrent: Maximum number of concurrent downloads allowed
        """
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.active_downloads = {}  # task_id -> DownloadTask
        self.queue_counter = 0
        self.task_id_counter = 0
        logger.info(f"DownloadManager initialized with max_concurrent={max_concurrent}")
    
    def get_queue_status(self) -> dict:
        """
        Get current queue status.
        
        Returns:
            dict with 'active', 'max', and 'waiting' counts
        """
        active_count = len(self.active_downloads)
        waiting_count = max(0, self.queue_counter - active_count)
        
        return {
            'active': active_count,
            'max': self.max_concurrent,
            'waiting': waiting_count,
            'total': self.queue_counter
        }
    
    async def download(
        self,
        download_func: Callable,
        task_type: str,
        url: str,
        user_id: int,
        chat_id: int,
        progress_callback: Optional[Callable] = None
    ) -> None:
        """
        Queue and execute a download with concurrency control.
        
        Args:
            download_func: The blocking download function to execute
            task_type: Type of download ('youtube' or 'telegram')
            url: URL or identifier for the download
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            progress_callback: Optional callback for progress updates
        """
        # Increment queue counter and assign task ID
        self.queue_counter += 1
        self.task_id_counter += 1
        task_id = self.task_id_counter
        
        task = DownloadTask(
            url=url,
            user_id=user_id,
            chat_id=chat_id,
            task_type=task_type,
            queued_at=datetime.now(),
            task_id=task_id
        )
        
        logger.info(
            f"Download queued: task_id={task_id}, type={task_type}, "
            f"user={user_id}, queue_position={self.queue_counter}"
        )
        
        try:
            # Acquire semaphore (wait if at limit)
            async with self.semaphore:
                # Add to active downloads
                self.active_downloads[task_id] = task
                logger.info(
                    f"Download started: task_id={task_id}, "
                    f"active={len(self.active_downloads)}/{self.max_concurrent}"
                )
                
                # Run blocking download function in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self.executor, download_func)
                
                logger.info(f"Download completed: task_id={task_id}")
                
        except Exception as e:
            logger.error(f"Download failed: task_id={task_id}, error={e}")
            raise
        finally:
            # Remove from active downloads
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]
            self.queue_counter = max(0, self.queue_counter - 1)
    
    def shutdown(self):
        """Shutdown the thread pool executor"""
        logger.info("Shutting down DownloadManager")
        self.executor.shutdown(wait=True)


# Global singleton instance
_download_manager: Optional[DownloadManager] = None


def get_download_manager(max_concurrent: int = 3) -> DownloadManager:
    """
    Get or create the global DownloadManager singleton.
    
    Args:
        max_concurrent: Maximum concurrent downloads (only used on first call)
    
    Returns:
        DownloadManager instance
    """
    global _download_manager
    if _download_manager is None:
        _download_manager = DownloadManager(max_concurrent)
    return _download_manager
