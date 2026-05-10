"""
DLHUB - Redis Queue Client
===========================
Async Redis client for queue operations.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class QueueClient:
    """Async Redis queue client."""

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client: Optional[aioredis.Redis] = None

        self.prefix = "dlhub:queue"
        self.jobs_key = f"{self.prefix}:jobs"
        self.pending_key = f"{self.prefix}:pending"
        self.processing_key = f"{self.prefix}:processing"
        self.completed_key = f"{self.prefix}:completed"
        self.failed_key = f"{self.prefix}:failed"

        self.progress_prefix = f"{self.prefix}:progress"
        self.results_prefix = f"{self.prefix}:results"
        self.stats_key = f"{self.prefix}:stats"

    async def connect(self):
        """Connect to Redis."""
        if not self._client:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS
            )
            logger.info(f"Connected to Redis at {self.redis_url}")

    async def close(self):
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Redis connection closed")

    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client."""
        if not self._client:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    async def ping(self) -> bool:
        """Check Redis connection."""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def add_job(self, job_id: str, job_data: Dict[str, Any], priority: int = 1) -> bool:
        """Add job to pending queue."""
        try:
            job_data["added_at"] = datetime.utcnow().isoformat()
            job_data["priority"] = priority

            await self.client.hset(self.jobs_key, job_id, json.dumps(job_data))

            score = priority * 1000000 - int(datetime.utcnow().timestamp())
            await self.client.zadd(self.pending_key, {job_id: score})

            await self._increment_stat("jobs_added")
            logger.info(f"Job {job_id} added to queue with priority {priority}")
            return True
        except Exception as e:
            logger.error(f"Failed to add job {job_id}: {e}")
            return False

    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data."""
        try:
            data = await self.client.hget(self.jobs_key, job_id)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None

    async def update_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Update job data."""
        try:
            await self.client.hset(self.jobs_key, job_id, json.dumps(job_data))
            return True
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            return False

    async def delete_job(self, job_id: str) -> bool:
        """Delete job from all queues."""
        try:
            await self.client.hdel(self.jobs_key, job_id)
            await self.client.zrem(self.pending_key, job_id)
            await self.client.zrem(self.processing_key, job_id)
            await self.client.zrem(self.completed_key, job_id)
            await self.client.zrem(self.failed_key, job_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False

    async def get_next_job(self) -> Optional[str]:
        """Get next job from pending queue."""
        try:
            result = await self.client.zpopmin(self.pending_key)
            if result:
                job_id = result[0][0].decode() if isinstance(result[0][0], bytes) else result[0][0]
                await self.client.zadd(self.processing_key, {job_id: datetime.utcnow().timestamp()})
                return job_id
            return None
        except Exception as e:
            logger.error(f"Failed to get next job: {e}")
            return None

    async def complete_job(self, job_id: str) -> bool:
        """Move job to completed."""
        try:
            processing_score = await self.client.zscore(self.processing_key, job_id)
            if processing_score:
                await self.client.zrem(self.processing_key, job_id)
                await self.client.zadd(self.completed_key, {job_id: datetime.utcnow().timestamp()})
                await self._increment_stat("jobs_completed")
                logger.info(f"Job {job_id} completed")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to complete job {job_id}: {e}")
            return False

    async def fail_job(self, job_id: str, error: str) -> bool:
        """Move job to failed."""
        try:
            await self.client.zrem(self.processing_key, job_id)
            await self.client.zadd(self.failed_key, {job_id: datetime.utcnow().timestamp()})

            job_data = await self.get_job(job_id)
            if job_data:
                job_data["error"] = error
                job_data["failed_at"] = datetime.utcnow().isoformat()
                await self.update_job(job_id, job_data)

            await self._increment_stat("jobs_failed")
            logger.error(f"Job {job_id} failed: {error}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as failed: {e}")
            return False

    async def get_queue_size(self) -> Dict[str, int]:
        """Get queue sizes."""
        try:
            return {
                "pending": await self.client.zcard(self.pending_key),
                "processing": await self.client.zcard(self.processing_key),
                "completed": await self.client.zcard(self.completed_key),
                "failed": await self.client.zcard(self.failed_key),
                "total": await self.client.hlen(self.jobs_key),
            }
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return {"pending": 0, "processing": 0, "completed": 0, "failed": 0, "total": 0}

    async def get_pending_jobs(self, limit: int = 100) -> List[str]:
        """Get pending job IDs."""
        try:
            results = await self.client.zrange(self.pending_key, 0, limit - 1)
            return [r.decode() if isinstance(r, bytes) else r for r in results]
        except Exception as e:
            logger.error(f"Failed to get pending jobs: {e}")
            return []

    async def get_processing_jobs(self, limit: int = 100) -> List[str]:
        """Get processing job IDs."""
        try:
            results = await self.client.zrange(self.processing_key, 0, limit - 1)
            return [r.decode() if isinstance(r, bytes) else r for r in results]
        except Exception as e:
            logger.error(f"Failed to get processing jobs: {e}")
            return []

    async def set_progress(self, job_id: str, progress: Dict[str, Any]) -> bool:
        """Set job progress."""
        try:
            key = f"{self.progress_prefix}:{job_id}"
            await self.client.hset(key, mapping=progress)
            await self.client.expire(key, 3600)
            return True
        except Exception as e:
            logger.error(f"Failed to set progress for {job_id}: {e}")
            return False

    async def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job progress."""
        try:
            key = f"{self.progress_prefix}:{job_id}"
            data = await self.client.hgetall(key)
            return data if data else None
        except Exception as e:
            logger.error(f"Failed to get progress for {job_id}: {e}")
            return None

    async def set_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Set job result."""
        try:
            key = f"{self.results_prefix}:{job_id}"
            await self.client.hset(key, mapping=result)
            await self.client.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"Failed to set result for {job_id}: {e}")
            return False

    async def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job result."""
        try:
            key = f"{self.results_prefix}:{job_id}"
            data = await self.client.hgetall(key)
            return data if data else None
        except Exception as e:
            logger.error(f"Failed to get result for {job_id}: {e}")
            return None

    async def _increment_stat(self, stat: str) -> bool:
        """Increment a statistic."""
        try:
            await self.client.hincrby(self.stats_key, stat, 1)
            return True
        except Exception:
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        try:
            stats = await self.client.hgetall(self.stats_key)
            queue_sizes = await self.get_queue_size()
            return {
                "stats": stats,
                "queues": queue_sizes
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    async def clear_completed(self, before_timestamp: float = None) -> int:
        """Clear completed jobs older than timestamp."""
        try:
            if before_timestamp is None:
                before_timestamp = datetime.utcnow().timestamp() - 86400

            count = await self.client.zremrangebyscore(self.completed_key, 0, before_timestamp)
            logger.info(f"Cleared {count} completed jobs")
            return count
        except Exception as e:
            logger.error(f"Failed to clear completed jobs: {e}")
            return 0


queue_client = QueueClient()