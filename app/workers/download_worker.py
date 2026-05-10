"""
DLHUB - Download Worker
========================
Async worker for processing download jobs.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import asyncio
import logging
from datetime import datetime

from app.config import settings
from app.queue.manager import queue_manager
from app.queue.client import queue_client
from app.services.yt_dlp_service import yt_dlp_service
from app.constants import DownloadStatus
from app.database import get_db_sync
from app.models.job import Job

logger = logging.getLogger(__name__)


class DownloadWorker:
    """Async download worker that processes jobs from the queue."""

    def __init__(self, worker_id: str = None):
        self.worker_id = worker_id or f"worker-{asyncio.get_event_loop().time_ns()}"
        self.running = False
        self.current_job = None
        self.concurrency = settings.WORKER_COUNT

    async def start(self):
        """Start the worker."""
        logger.info(f"Starting download worker: {self.worker_id}")
        await queue_manager.initialize()
        await queue_client.connect()
        self.running = True
        await self._process_loop()

    async def stop(self):
        """Stop the worker."""
        logger.info(f"Stopping download worker: {self.worker_id}")
        self.running = False
        await queue_manager.close()
        await queue_client.close()

    async def _process_loop(self):
        """Main processing loop."""
        while self.running:
            try:
                if await queue_manager.is_queue_paused():
                    await asyncio.sleep(5)
                    continue

                job_id = await queue_client.get_next_job()
                if not job_id:
                    await asyncio.sleep(2)
                    continue

                await self._process_job(job_id)

            except asyncio.CancelledError:
                logger.info(f"Worker {self.worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)

    async def _process_job(self, job_id: str):
        """Process a single job."""
        logger.info(f"Worker {self.worker_id} processing job: {job_id}")
        self.current_job = job_id

        job_data = await queue_client.get_job(job_id)
        if not job_data:
            logger.error(f"Job {job_id} not found")
            return

        try:
            await queue_client.set_progress(job_id, {
                "status": "processing",
                "worker": self.worker_id,
                "started_at": datetime.utcnow().isoformat(),
            })

            result = await yt_dlp_service.download(
                url=job_data["url"],
                download_type=job_data.get("type", "video"),
                quality=job_data.get("quality"),
                output_format=job_data.get("output_format"),
                filename=job_data.get("filename"),
                format_string=job_data.get("format_string"),
                thumbnail=job_data.get("thumbnail", True),
                metadata=job_data.get("metadata", True),
                chapters=job_data.get("chapters", True),
                subtitles=job_data.get("subtitles", True),
            )

            await queue_client.complete_job(job_id)
            await queue_client.set_result(job_id, {
                "status": "completed",
                "file_path": result.get("file_path"),
                "file_name": result.get("file_name"),
                "file_size": result.get("file_size"),
            })

            await self._update_db_job_status(job_id, DownloadStatus.COMPLETED, result)

            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            await queue_client.fail_job(job_id, str(e))
            await self._update_db_job_status(job_id, DownloadStatus.FAILED, {"error": str(e)})

        finally:
            self.current_job = None

    async def _update_db_job_status(self, job_id: str, status: DownloadStatus, result: dict):
        """Update job status in PostgreSQL."""
        try:
            with get_db_sync() as db:
                from sqlalchemy import select
                result_db = db.execute(select(Job).where(Job.id == job_id))
                job = result_db.scalar_one_or_none()

                if job:
                    job.status = status
                    if status == DownloadStatus.COMPLETED:
                        job.file_path = result.get("file_path")
                        job.file_name = result.get("file_name")
                        job.file_size = result.get("file_size")
                        job.completed_at = datetime.utcnow()
                        job.progress = 100.0
                    elif status == DownloadStatus.FAILED:
                        job.error_message = result.get("error")
                        job.completed_at = datetime.utcnow()

                    db.commit()
        except Exception as e:
            logger.error(f"Failed to update DB job {job_id}: {e}")

    async def get_status(self) -> dict:
        """Get worker status."""
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "current_job": self.current_job,
        }


async def run_worker():
    """Run a single worker."""
    worker = DownloadWorker()
    await worker.start()


if __name__ == "__main__":
    asyncio.run(run_worker())