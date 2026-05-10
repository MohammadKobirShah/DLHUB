"""
DLHUB - Admin Router
====================
Admin operations and management endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
import time
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, func

from app.config import settings
from app.database import get_db, async_session_maker
from app.models.job import Job
from app.constants import DownloadStatus
from app.queue.client import queue_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/admin/overview")
async def admin_overview():
    """Get admin dashboard overview."""
    try:
        async with async_session_maker() as session:
            total_jobs = await session.scalar(select(func.count(Job.id)))

            pending = await session.scalar(
                select(func.count(Job.id)).where(Job.status == DownloadStatus.PENDING)
            )
            processing = await session.scalar(
                select(func.count(Job.id)).where(Job.status == DownloadStatus.PROCESSING)
            )
            completed = await session.scalar(
                select(func.count(Job.id)).where(Job.status == DownloadStatus.COMPLETED)
            )
            failed = await session.scalar(
                select(func.count(Job.id)).where(Job.status == DownloadStatus.FAILED)
            )

            total_size = await session.scalar(
                select(func.sum(Job.file_size)).where(Job.status == DownloadStatus.COMPLETED)
            ) or 0

            today = datetime.utcnow().date()
            jobs_today = await session.scalar(
                select(func.count(Job.id)).where(func.date(Job.created_at) == today)
            )

            recent_failed = await session.execute(
                select(Job).where(Job.status == DownloadStatus.FAILED)
                .order_by(Job.updated_at.desc()).limit(5)
            )
            failed_jobs = recent_failed.scalars().all()

        download_path = Path(settings.DOWNLOAD_DIR)
        disk_usage = {}
        if download_path.exists():
            import shutil
            usage = shutil.disk_usage(str(download_path))
            disk_usage = {
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": round(usage.used / usage.total * 100, 2)
            }

        queue_sizes = await queue_client.get_queue_size()

        return {
            "jobs": {
                "total": total_jobs,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed,
                "jobs_today": jobs_today
            },
            "storage": {
                "total_downloads_size": total_size,
                "disk": disk_usage
            },
            "queue": queue_sizes,
            "recent_failures": [
                {"id": str(j.id), "url": j.url[:50], "error": j.error_message}
                for j in failed_jobs
            ]
        }
    except Exception as e:
        logger.error(f"Admin overview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/jobs")
async def admin_list_jobs(
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|status)$"),
    order: str = Query("desc", pattern="^(asc|desc)$")
):
    """List all jobs with filters and pagination."""
    try:
        async with async_session_maker() as session:
            query = select(Job)

            if status:
                try:
                    query = query.where(Job.status == DownloadStatus(status))
                except ValueError:
                    pass

            if job_type:
                query = query.where(Job.job_type == job_type)

            if sort_by == "created_at":
                sort_col = Job.created_at
            elif sort_by == "updated_at":
                sort_col = Job.updated_at
            else:
                sort_col = Job.status

            if order == "desc":
                query = query.order_by(sort_col.desc())
            else:
                query = query.order_by(sort_col.asc())

            total_result = await session.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = total_result.scalar()

            query = query.offset((page - 1) * page_size).limit(page_size)
            result = await session.execute(query)
            jobs = result.scalars().all()

            return {
                "jobs": [j.to_dict() for j in jobs],
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
    except Exception as e:
        logger.error(f"Admin list jobs failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/job/{job_id}/force-cancel")
async def admin_force_cancel_job(job_id: str):
    """Force cancel a job."""
    try:
        from sqlalchemy import update
        async with async_session_maker() as session:
            await session.execute(
                update(Job).where(Job.id == job_id).values(
                    status=DownloadStatus.CANCELLED,
                    completed_at=datetime.utcnow()
                )
            )
            await session.commit()

        await queue_client.delete_job(job_id)

        return {"success": True, "message": f"Job {job_id} force cancelled"}
    except Exception as e:
        logger.error(f"Force cancel failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/cleanup/expired")
async def admin_cleanup_expired(
    days: int = Query(7, ge=1, description="Delete files older than N days"),
    dry_run: bool = Query(False)
):
    """Clean up expired/completed jobs and old files."""
    try:
        deleted_jobs = 0
        deleted_files = 0
        freed_space = 0

        cutoff = datetime.utcnow() - timedelta(days=days)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Job).where(
                    Job.status == DownloadStatus.COMPLETED,
                    Job.completed_at < cutoff
                )
            )
            old_jobs = result.scalars().all()

            if not dry_run:
                for job in old_jobs:
                    if job.file_path and os.path.exists(job.file_path):
                        try:
                            freed_space += os.path.getsize(job.file_path)
                            os.remove(job.file_path)
                            deleted_files += 1
                        except Exception:
                            pass

                    await session.delete(job)
                    deleted_jobs += 1

                await session.commit()

        if not dry_run and settings.DOWNLOAD_DIR:
            download_path = Path(settings.DOWNLOAD_DIR)
            if download_path.exists():
                current_time = time.time()
                file_cutoff = current_time - (days * 86400)

                for f in download_path.iterdir():
                    if f.is_file() and f.stat().st_mtime < file_cutoff:
                        try:
                            freed_space += f.stat().st_size
                            f.unlink()
                            deleted_files += 1
                        except Exception:
                            pass

        return {
            "success": True,
            "dry_run": dry_run,
            "deleted_jobs": deleted_jobs,
            "deleted_files": deleted_files,
            "freed_space_bytes": freed_space
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/cleanup/corrupted")
async def admin_cleanup_corrupted():
    """Clean up corrupted/incomplete downloads."""
    try:
        deleted_count = 0
        freed_space = 0

        async with async_session_maker() as session:
            result = await session.execute(
                select(Job).where(
                    Job.status == DownloadStatus.FAILED,
                    Job.error_message.like("%incomplete%")
                )
            )
            corrupted = result.scalars().all()

            for job in corrupted:
                if job.file_path and os.path.exists(job.file_path):
                    try:
                        freed_space += os.path.getsize(job.file_path)
                        os.remove(job.file_path)
                        deleted_count += 1
                    except Exception:
                        pass

                await session.delete(job)

            await session.commit()

        return {
            "success": True,
            "deleted_count": deleted_count,
            "freed_space_bytes": freed_space
        }
    except Exception as e:
        logger.error(f"Corrupted cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/analytics")
async def admin_analytics(
    days: int = Query(30, ge=1, le=365)
):
    """Get usage analytics."""
    try:
        async with async_session_maker() as session:
            start_date = datetime.utcnow() - timedelta(days=days)

            daily_stats = []
            for i in range(days):
                day = start_date + timedelta(days=i)
                next_day = day + timedelta(days=1)

                count = await session.scalar(
                    select(func.count(Job.id)).where(
                        Job.created_at >= day,
                        Job.created_at < next_day
                    )
                )

                completed = await session.scalar(
                    select(func.count(Job.id)).where(
                        Job.status == DownloadStatus.COMPLETED,
                        Job.created_at >= day,
                        Job.created_at < next_day
                    )
                )

                total_size = await session.scalar(
                    select(func.sum(Job.file_size)).where(
                        Job.status == DownloadStatus.COMPLETED,
                        Job.completed_at >= day,
                        Job.completed_at < next_day
                    )
                )

                daily_stats.append({
                    "date": day.date().isoformat(),
                    "jobs_created": count,
                    "jobs_completed": completed,
                    "bytes_downloaded": total_size or 0
                })

            type_stats = {}
            for dtype in ["video", "audio", "playlist", "custom"]:
                count = await session.scalar(
                    select(func.count(Job.id)).where(
                        Job.job_type == dtype,
                        Job.created_at >= start_date
                    )
                )
                type_stats[dtype] = count

            format_stats = {}
            result = await session.execute(
                select(Job.output_format, func.count(Job.id))
                .where(Job.created_at >= start_date)
                .group_by(Job.output_format)
            )
            for row in result:
                format_stats[row[0] or "unknown"] = row[1]

            return {
                "period_days": days,
                "daily_stats": daily_stats,
                "by_type": type_stats,
                "by_format": format_stats
            }
    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/cache")
async def admin_cache_stats():
    """Get cache statistics."""
    try:
        stats = await queue_client.get_stats()
        queue_sizes = await queue_client.get_queue_size()

        return {
            "redis_stats": stats.get("stats", {}),
            "queue_sizes": queue_sizes
        }
    except Exception as e:
        logger.error(f"Cache stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/cache/clear")
async def admin_clear_cache():
    """Clear Redis cache."""
    try:
        await queue_client.clear_completed(0)
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/workers/detail")
async def admin_workers_detail():
    """Get detailed worker information."""
    try:
        processing = await queue_client.get_processing_jobs(100)

        return {
            "active_jobs": len(processing),
            "workers": [
                {
                    "worker_id": f"worker-{i}",
                    "status": "idle" if i >= len(processing) else "busy",
                    "current_job": processing[i]["job_id"] if i < len(processing) else None
                }
                for i in range(settings.WORKER_COUNT)
            ],
            "config": {
                "worker_count": settings.WORKER_COUNT,
                "worker_timeout": settings.WORKER_TIMEOUT,
                "max_concurrent": settings.MAX_CONCURRENT_DOWNLOADS
            }
        }
    except Exception as e:
        logger.error(f"Workers detail failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/config/reload")
async def admin_reload_config():
    """Reload configuration."""
    try:
        from app.config import get_settings
        settings_instance = get_settings()
        settings_instance.__init__()

        return {"success": True, "message": "Configuration reloaded"}
    except Exception as e:
        logger.error(f"Config reload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/downloads/top")
async def admin_top_downloads(
    limit: int = Query(10, ge=1, le=50)
):
    """Get top downloaded files."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Job)
                .where(Job.status == DownloadStatus.COMPLETED)
                .order_by(Job.file_size.desc())
                .limit(limit)
            )
            jobs = result.scalars().all()

            return {
                "downloads": [
                    {
                        "id": str(j.id),
                        "title": j.title,
                        "file_name": j.file_name,
                        "file_size": j.file_size,
                        "uploader": j.uploader,
                        "completed_at": j.completed_at.isoformat() if j.completed_at else None
                    }
                    for j in jobs
                ]
            }
    except Exception as e:
        logger.error(f"Top downloads failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))