import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class CancelledError(Exception):
    """Raised when a download task is cancelled."""
    pass


@dataclass
class DownloadTask:
    """Represents a download task in the queue"""
    url: str
    user_id: int
    chat_id: int
    task_type: str  # 'youtube' or 'telegram'
    queued_at: datetime
    task_id: int
    future: asyncio.Future = None
    cancelled: bool = False


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

    def get_task(self, task_id: int) -> Optional[DownloadTask]:
        """Get a task by ID."""
        return self.active_downloads.get(task_id)

    def cancel_task(self, task_id: int) -> bool:
        """
        Mark a task as cancelled.
        
        Returns:
            bool: True if task was found and marked, False otherwise
        """
        task = self.get_task(task_id)
        if task:
            task.cancelled = True
            logger.info(f"Task {task_id} marked as cancelled")
            return True
        return False
    
    async def submit_download(
        self,
        download_func: Callable,
        task_type: str,
        url: str,
        user_id: int,
        chat_id: int,
        progress_callback: Optional[Callable] = None
    ) -> tuple[int, asyncio.Future]:
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
            task_id=task_id,
            future=asyncio.get_event_loop().create_future()
        )
        
        logger.info(
            f"Download queued: task_id={task_id}, type={task_type}, "
            f"user={user_id}, queue_position={self.queue_counter}"
        )
        
        async def _execute_download():
            try:
                # Acquire semaphore (wait if at limit)
                async with self.semaphore:
                    # check for cancellation before starting
                    if task.cancelled:
                         logger.info(f"Task {task_id} cancelled before start")
                         raise CancelledError("Task cancelled before start")
                    
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
                    if not task.future.done():
                        task.future.set_result(True)
                    
            except Exception as e:
                logger.error(f"Download failed: task_id={task_id}, error={e}")
                if not task.future.done():
                    task.future.set_exception(e)
                raise
            finally:
                # Remove from active downloads
                if task_id in self.active_downloads:
                    del self.active_downloads[task_id]
                self.queue_counter = max(0, self.queue_counter - 1)

        # Start execution in background
        asyncio.create_task(_execute_download())
        
        return task_id, task.future
    
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
