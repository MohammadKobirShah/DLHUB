"""
DLHUB - Worker Pool
===================
Manages multiple async workers.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import asyncio
import logging
from typing import List

from app.config import settings
from app.workers.download_worker import DownloadWorker

logger = logging.getLogger(__name__)


class WorkerPool:
    """Manages a pool of download workers."""

    def __init__(self, worker_count: int = None):
        self.worker_count = worker_count or settings.WORKER_COUNT
        self.workers: List[DownloadWorker] = []
        self.tasks: List[asyncio.Task] = []
        self.running = False

    async def start(self):
        """Start all workers in the pool."""
        logger.info(f"Starting worker pool with {self.worker_count} workers")
        self.running = True

        for i in range(self.worker_count):
            worker = DownloadWorker(worker_id=f"worker-{i}")
            self.workers.append(worker)

            task = asyncio.create_task(worker.start())
            self.tasks.append(task)

        logger.info(f"Worker pool started with {len(self.workers)} workers")

    async def stop(self):
        """Stop all workers in the pool."""
        logger.info("Stopping worker pool")
        self.running = False

        for task in self.tasks:
            task.cancel()

        await asyncio.gather(*self.tasks, return_exceptions=True)

        for worker in self.workers:
            try:
                await worker.stop()
            except Exception as e:
                logger.error(f"Error stopping worker {worker.worker_id}: {e}")

        logger.info("Worker pool stopped")

    async def restart_worker(self, worker_id: str):
        """Restart a specific worker."""
        for i, worker in enumerate(self.workers):
            if worker.worker_id == worker_id:
                logger.info(f"Restarting worker {worker_id}")

                self.tasks[i].cancel()
                await asyncio.sleep(1)

                new_worker = DownloadWorker(worker_id=worker_id)
                self.workers[i] = new_worker
                self.tasks[i] = asyncio.create_task(new_worker.start())

                logger.info(f"Worker {worker_id} restarted")
                return True

        return False

    def get_status(self) -> dict:
        """Get status of all workers."""
        return {
            "pool_size": self.worker_count,
            "active_workers": len([w for w in self.workers if w.running]),
            "running": self.running,
            "workers": [w.get_status() for w in self.workers]
        }

    async def scale(self, new_count: int):
        """Scale the worker pool."""
        if new_count < 1 or new_count > 20:
            logger.error(f"Invalid worker count: {new_count}")
            return

        logger.info(f"Scaling worker pool from {self.worker_count} to {new_count}")

        if new_count > self.worker_count:
            for i in range(self.worker_count, new_count):
                worker = DownloadWorker(worker_id=f"worker-{i}")
                self.workers.append(worker)
                task = asyncio.create_task(worker.start())
                self.tasks.append(task)

        elif new_count < self.worker_count:
            for i in range(new_count, self.worker_count):
                if i < len(self.tasks):
                    self.tasks[i].cancel()
                if i < len(self.workers):
                    await self.workers[i].stop()

            self.workers = self.workers[:new_count]
            self.tasks = self.tasks[:new_count]

        self.worker_count = new_count
        logger.info(f"Worker pool scaled to {new_count} workers")


worker_pool = WorkerPool()