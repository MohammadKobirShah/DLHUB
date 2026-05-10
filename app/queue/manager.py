"""
DLHUB - Queue Manager
======================
High-level queue management.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.queue.client import queue_client
from app.constants import DownloadStatus, DownloadType

logger = logging.getLogger(__name__)


class JobPriority:
    """Job priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class QueueManager:
    """Manages download queue operations."""

    def __init__(self):
        self.client = queue_client

    async def initialize(self):
        """Initialize queue system."""
        await self.client.connect()
        logger.info("Queue manager initialized")

    async def close(self):
        """Close queue system."""
        await self.client.close()
        logger.info("Queue manager closed")

    async def enqueue_download(
        self,
        url: str,
        download_type: str = "video",
        quality: Optional[str] = None,
        output_format: Optional[str] = None,
        priority: int = JobPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add download to queue.

        Args:
            url: URL to download
            download_type: Type (video, audio, playlist)
            quality: Quality preset
            output_format: Output format
            priority: Job priority (0-3)
            metadata: Additional metadata

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job_data = {
            "job_id": job_id,
            "url": url,
            "type": download_type,
            "quality": quality,
            "output_format": output_format,
            "status": DownloadStatus.PENDING.value,
            "priority": priority,
            "metadata": metadata or {},
            "retries": 0,
            "max_retries": 3,
            "created_at": datetime.utcnow().isoformat(),
        }

        await self.client.add_job(job_id, job_data, priority)
        logger.info(f"Download enqueued: {job_id} ({download_type})")

        return job_id

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status from queue."""
        job_data = await self.client.get_job(job_id)
        if not job_data:
            return None

        progress = await self.client.get_progress(job_id)
        if progress:
            job_data["progress"] = progress

        result = await self.client.get_result(job_id)
        if result:
            job_data["result"] = result

        return job_data

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        job_data = await self.client.get_job(job_id)
        if not job_data:
            return False

        job_data["status"] = DownloadStatus.CANCELLED.value
        job_data["cancelled_at"] = datetime.utcnow().isoformat()

        await self.client.update_job(job_id, job_data)
        await self.client.delete_job(job_id)

        logger.info(f"Job cancelled: {job_id}")
        return True

    async def retry_job(self, job_id: str) -> bool:
        """Retry a failed job."""
        job_data = await self.client.get_job(job_id)
        if not job_data:
            return False

        if job_data.get("status") != DownloadStatus.FAILED.value:
            return False

        job_data["status"] = DownloadStatus.PENDING.value
        job_data["retries"] = job_data.get("retries", 0) + 1
        job_data["error"] = None

        priority = job_data.get("priority", JobPriority.NORMAL)
        await self.client.add_job(job_id, job_data, priority)

        logger.info(f"Job requeued: {job_id} (attempt {job_data['retries']})")
        return True

    async def pause_queue(self) -> bool:
        """Pause queue processing."""
        try:
            await self.client.client.set(f"{self.client.prefix}:paused", "1")
            logger.info("Queue paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause queue: {e}")
            return False

    async def resume_queue(self) -> bool:
        """Resume queue processing."""
        try:
            await self.client.client.delete(f"{self.client.prefix}:paused")
            logger.info("Queue resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume queue: {e}")
            return False

    async def is_queue_paused(self) -> bool:
        """Check if queue is paused."""
        try:
            result = await self.client.client.get(f"{self.client.prefix}:paused")
            return result == "1"
        except Exception:
            return False

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        queue_sizes = await self.client.get_queue_size()
        stats = await self.client.get_stats()
        is_paused = await self.is_queue_paused()

        return {
            "paused": is_paused,
            "queue_sizes": queue_sizes,
            "stats": stats.get("stats", {}),
        }

    async def get_pending_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending jobs with details."""
        job_ids = await self.client.get_pending_jobs(limit)
        jobs = []

        for job_id in job_ids:
            job_data = await self.client.get_job(job_id)
            if job_data:
                jobs.append(job_data)

        return jobs

    async def get_processing_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get currently processing jobs."""
        job_ids = await self.client.get_processing_jobs(limit)
        jobs = []

        for job_id in job_ids:
            job_data = await self.client.get_job(job_id)
            if job_data:
                progress = await self.client.get_progress(job_id)
                if progress:
                    job_data["progress"] = progress
                jobs.append(job_data)

        return jobs

    async def update_job_progress(
        self,
        job_id: str,
        progress: float,
        speed: Optional[str] = None,
        eta: Optional[int] = None,
        downloaded: Optional[int] = None,
        total: Optional[int] = None
    ) -> bool:
        """Update job progress."""
        progress_data = {
            "progress": str(progress),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if speed:
            progress_data["speed"] = speed
        if eta is not None:
            progress_data["eta"] = str(eta)
        if downloaded is not None:
            progress_data["downloaded"] = str(downloaded)
        if total is not None:
            progress_data["total"] = str(total)

        return await self.client.set_progress(job_id, progress_data)

    async def set_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Set job completion result."""
        result["completed_at"] = datetime.utcnow().isoformat()
        return await self.client.set_result(job_id, result)

    async def cleanup_old_jobs(self, days: int = 7) -> int:
        """Clean up old completed jobs."""
        import time
        cutoff = time.time() - (days * 86400)
        return await self.client.clear_completed(cutoff)


queue_manager = QueueManager()