"""
DLHUB - System Router
======================
Health, version, stats, and system endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.config import settings
from app.database import get_db
from app.models.job import Job
from app.constants import DownloadStatus, API_VERSION
from app.schemas.response import (
    HealthResponse,
    VersionResponse,
    SystemStatsResponse,
    StorageResponse,
)
from app.services.yt_dlp_service import yt_dlp_service

router = APIRouter()


@router.get("/system/health", response_model=HealthResponse)
async def health_check(db=None):
    """
    System health check.

    Returns status of API, database, redis, and storage.
    """
    health = HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.VERSION,
        timestamp=datetime.utcnow().isoformat()
    )

    try:
        from app.database import engine
        async with engine.connect() as conn:
            await conn.execute(select(1))
        health.database = "connected"
    except Exception as e:
        health.database = f"error: {str(e)}"
        health.status = "degraded"

    try:
        import redis.asyncio as aioredis
        r = await aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        health.redis = "connected"
    except Exception as e:
        health.redis = f"error: {str(e)}"

    try:
        download_path = Path(settings.DOWNLOAD_DIR)
        if download_path.exists():
            health.storage = "available"
        else:
            health.storage = "not_found"
    except Exception as e:
        health.storage = f"error: {str(e)}"

    return health


@router.get("/system/version", response_model=VersionResponse)
async def version_info():
    """
    Get version information for all components.
    """
    yt_version = "unknown"
    ff_version = "unknown"

    try:
        yt_version = yt_dlp_service.get_version()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            ff_version = result.stdout.split("\n")[0].replace("ffmpeg version ", "")
    except Exception:
        pass

    import platform
    python_version = platform.python_version()

    return VersionResponse(
        app_name=settings.APP_NAME,
        version=settings.VERSION,
        api_version=API_VERSION,
        yt_dlp_version=yt_version,
        ffmpeg_version=ff_version,
        python_version=python_version,
    )


@router.get("/system/stats", response_model=SystemStatsResponse)
async def system_stats(db=None):
    """
    Get system statistics.
    """
    from app.database import async_session_maker

    async with async_session_maker() as session:
        total_result = await session.execute(select(func.count(Job.id)))
        total_jobs = total_result.scalar()

        pending_result = await session.execute(
            select(func.count(Job.id)).where(Job.status == DownloadStatus.PENDING)
        )
        pending_jobs = pending_result.scalar()

        processing_result = await session.execute(
            select(func.count(Job.id)).where(Job.status == DownloadStatus.PROCESSING)
        )
        processing_jobs = processing_result.scalar()

        completed_result = await session.execute(
            select(func.count(Job.id)).where(Job.status == DownloadStatus.COMPLETED)
        )
        completed_jobs = completed_result.scalar()

        failed_result = await session.execute(
            select(func.count(Job.id)).where(Job.status == DownloadStatus.FAILED)
        )
        failed_jobs = failed_result.scalar()

        cancelled_result = await session.execute(
            select(func.count(Job.id)).where(Job.status == DownloadStatus.CANCELLED)
        )
        cancelled_jobs = cancelled_result.scalar()

        size_result = await session.execute(
            select(func.sum(Job.file_size)).where(Job.status == DownloadStatus.COMPLETED)
        )
        total_size = size_result.scalar() or 0

    from app.database import engine
    start_time = None
    try:
        async with engine.connect() as conn:
            result = await conn.execute(select(1))
            start_time = datetime.utcnow()
    except Exception:
        pass

    uptime = "unknown"
    if start_time:
        diff = datetime.utcnow() - start_time
        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"

    return SystemStatsResponse(
        total_jobs=total_jobs,
        pending_jobs=pending_jobs,
        processing_jobs=processing_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        cancelled_jobs=cancelled_jobs,
        total_downloads=completed_jobs,
        total_size=total_size,
        active_workers=settings.WORKER_COUNT,
        queue_size=pending_jobs,
        uptime=uptime
    )


@router.get("/system/storage", response_model=StorageResponse)
async def storage_info():
    """
    Get storage usage information.
    """
    download_path = Path(settings.DOWNLOAD_DIR)

    if not download_path.exists():
        raise HTTPException(status_code=404, detail="Download directory not found")

    total_space = 0
    used_space = 0

    try:
        import shutil
        usage = shutil.disk_usage(str(download_path))
        total_space = usage.total
        used_space = usage.used
    except Exception:
        pass

    free_space = total_space - used_space
    usage_percent = (used_space / total_space * 100) if total_space > 0 else 0

    files = list(download_path.glob("*"))
    file_count = len([f for f in files if f.is_file()])

    largest_file = None
    if files:
        try:
            largest = max([f for f in files if f.is_file()], key=lambda x: x.stat().st_size)
            largest_file = {
                "name": largest.name,
                "size": largest.stat().st_size
            }
        except Exception:
            pass

    return StorageResponse(
        total_space=total_space,
        used_space=used_space,
        free_space=free_space,
        usage_percent=round(usage_percent, 2),
        download_count=file_count,
        largest_file=largest_file
    )


@router.get("/system/yt-dlp-version")
async def yt_dlp_version():
    """Get yt-dlp version."""
    try:
        version = yt_dlp_service.get_version()
        return {"version": version, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/ffmpeg-version")
async def ffmpeg_version():
    """Get FFmpeg version."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.split("\n")
            return {
                "version": lines[0],
                "full_output": result.stdout,
                "status": "ok"
            }
        else:
            raise HTTPException(status_code=500, detail="FFmpeg not available")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="FFmpeg not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/config")
async def get_config():
    """Get current configuration (non-sensitive values only)."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "download_dir": settings.DOWNLOAD_DIR,
        "temp_dir": settings.TEMP_DIR,
        "max_concurrent_downloads": settings.MAX_CONCURRENT_DOWNLOADS,
        "max_download_size": settings.MAX_DOWNLOAD_SIZE,
        "max_duration": settings.MAX_DURATION,
        "yt_dlp_format": settings.YTDLP_FORMAT,
        "yt_dlp_embed_thumbnail": settings.YTDLP_EMBED_THUMBNAIL,
        "yt_dlp_add_metadata": settings.YTDLP_ADD_METADATA,
        "yt_dlp_write_subtitles": settings.YTDLP_WRITE_SUBTITLES,
        "enable_rate_limit": settings.ENABLE_RATE_LIMIT,
        "enable_ssrf_protection": settings.ENABLE_SSRF_PROTECTION,
        "worker_count": settings.WORKER_COUNT,
    }


@router.post("/system/update-yt-dlp")
async def update_yt_dlp():
    """Update yt-dlp to latest version."""
    try:
        result = yt_dlp_service.update()
        if result.get("success"):
            return {"success": True, "message": "yt-dlp updated successfully", "output": result.get("output")}
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Update failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/metrics")
async def get_metrics():
    """Get Prometheus-style metrics."""
    from app.services.metrics_service import metrics
    return {"metrics": metrics.get_metrics()}