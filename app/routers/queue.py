"""
DLHUB - Queue Router
====================
Queue management endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.queue.manager import queue_manager, JobPriority
from app.schemas.request import QueueAddRequest

logger = logging.getLogger(__name__)

router = APIRouter()


class QueueStatusResponse(BaseModel):
    """Queue status response."""
    paused: bool
    queue_sizes: dict
    stats: dict


class JobStatusResponse(BaseModel):
    """Job status from queue."""
    job_id: str
    url: str
    type: str
    status: str
    priority: int
    progress: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class QueueJobListResponse(BaseModel):
    """List of queue jobs."""
    jobs: list
    total: int


@router.post("/queue/add", response_model=dict)
async def add_to_queue(request: QueueAddRequest):
    """Add download job to queue."""
    try:
        job_id = await queue_manager.enqueue_download(
            url=str(request.url),
            download_type=request.job_type,
            priority=request.priority or JobPriority.NORMAL,
            metadata=request.metadata
        )

        return {
            "success": True,
            "job_id": job_id,
            "message": "Job added to queue"
        }
    except Exception as e:
        logger.error(f"Failed to add job to queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/status/{job_id}")
async def get_queue_job_status(job_id: str):
    """Get job status from queue."""
    job = await queue_manager.get_job_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job


@router.get("/queue/status", response_model=QueueStatusResponse)
async def get_queue_status():
    """Get overall queue status."""
    status = await queue_manager.get_queue_status()
    return status


@router.get("/queue/pending", response_model=QueueJobListResponse)
async def get_pending_jobs(
    limit: int = Query(100, ge=1, le=500)
):
    """Get pending jobs."""
    jobs = await queue_manager.get_pending_jobs(limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/queue/processing", response_model=QueueJobListResponse)
async def get_processing_jobs(
    limit: int = Query(100, ge=1, le=500)
):
    """Get processing jobs."""
    jobs = await queue_manager.get_processing_jobs(limit)
    return {"jobs": jobs, "total": len(jobs)}


@router.post("/queue/pause")
async def pause_queue():
    """Pause queue processing."""
    success = await queue_manager.pause_queue()
    if success:
        return {"success": True, "message": "Queue paused"}
    raise HTTPException(status_code=500, detail="Failed to pause queue")


@router.post("/queue/resume")
async def resume_queue():
    """Resume queue processing."""
    success = await queue_manager.resume_queue()
    if success:
        return {"success": True, "message": "Queue resumed"}
    raise HTTPException(status_code=500, detail="Failed to resume queue")


@router.delete("/queue/{job_id}")
async def cancel_queue_job(job_id: str):
    """Cancel a queued job."""
    success = await queue_manager.cancel_job(job_id)
    if success:
        return {"success": True, "message": f"Job {job_id} cancelled"}
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@router.post("/queue/{job_id}/retry")
async def retry_queue_job(job_id: str):
    """Retry a failed job."""
    success = await queue_manager.retry_job(job_id)
    if success:
        return {"success": True, "message": f"Job {job_id} requeued"}
    raise HTTPException(status_code=400, detail=f"Job {job_id} cannot be retried")


@router.post("/queue/{job_id}/priority")
async def set_job_priority(job_id: str, priority: int = Query(0, ge=0, le=10)):
    """Set job priority."""
    job = await queue_manager.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job["priority"] = priority
    await queue_manager.client.update_job(job_id, job)

    return {"success": True, "priority": priority}


@router.get("/queue/list")
async def list_queue_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """List all queue jobs."""
    if status == "pending":
        jobs = await queue_manager.get_pending_jobs(page_size * page)
    elif status == "processing":
        jobs = await queue_manager.get_processing_jobs(page_size * page)
    else:
        pending = await queue_manager.get_pending_jobs(500)
        processing = await queue_manager.get_processing_jobs(500)
        jobs = processing + pending

    total = len(jobs)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = jobs[start:end]

    return {
        "jobs": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.post("/queue/clear")
async def clear_completed_jobs(days: int = Query(7, ge=1)):
    """Clear old completed jobs."""
    count = await queue_manager.cleanup_old_jobs(days)
    return {"success": True, "cleared_count": count}