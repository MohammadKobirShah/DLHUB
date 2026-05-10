"""
DLHUB - Download Router
=========================
Video/audio/playlist download endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.job import Job
from app.constants import DownloadStatus, DownloadType
from app.schemas.request import (
    VideoDownloadRequest,
    AudioDownloadRequest,
    PlaylistDownloadRequest,
    CustomDownloadRequest,
    RetryJobRequest,
)
from app.schemas.response import (
    JobResponse,
    JobStatusResponse,
    JobListResponse,
    FormatListResponse,
)
from app.services.yt_dlp_service import yt_dlp_service
from app.utils.sanitizer import sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_url(url: str) -> bool:
    """Basic URL validation."""
    if not url:
        return False

    if settings.ENABLE_SSRF_PROTECTION:
        blocked_patterns = [
            "localhost", "127.", "0.", "10.", "172.16.", "192.168.",
            "metadata.google.", "169.254.",
        ]
        url_lower = url.lower()
        for pattern in blocked_patterns:
            if pattern in url_lower:
                return False

    return True


async def _create_job(
    db: AsyncSession,
    url: str,
    job_type: DownloadType,
    request_params: dict
) -> Job:
    """Create a new download job."""
    job = Job(
        id=uuid.uuid4(),
        url=str(url),
        job_type=job_type,
        status=DownloadStatus.PENDING,
        output_format=request_params.get("format", "mp4"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    return job


async def _process_download(job_id: uuid.UUID, url: str, download_type: str, **kwargs):
    """Background task to process download."""
    from app.database import get_db_sync

    with get_db_sync() as db:
        job = db.get(Job, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        try:
            job.status = DownloadStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

            result = await yt_dlp_service.download(
                url=str(url),
                download_type=download_type,
                quality=kwargs.get("quality"),
                output_format=kwargs.get("format"),
                filename=kwargs.get("filename"),
                **kwargs
            )

            job.status = DownloadStatus.COMPLETED
            job.file_path = result.get("file_path")
            job.file_name = result.get("file_name")
            job.file_size = result.get("file_size")
            job.mime_type = f"video/{result.get('extension', 'mp4')}"
            job.completed_at = datetime.utcnow()
            job.progress = 100.0

            db.commit()
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            job.status = DownloadStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()


@router.post("/download/video", response_model=JobResponse)
async def download_video(
    request: VideoDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Download a single video.

    Quality presets: best, 2160p, 1440p, 1080p, 720p, 480p, 360p, 240p, 144p
    """
    if not _validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid or blocked URL")

    job = await _create_job(
        db,
        str(request.url),
        DownloadType.VIDEO,
        {
            "format": request.format,
            "quality": request.quality,
            "filename": request.filename,
            "thumbnail": request.thumbnail,
            "metadata": request.metadata,
            "chapters": request.chapters,
            "subtitles": request.subtitles,
        }
    )

    background_tasks.add_task(
        _process_download,
        job.id,
        str(request.url),
        "video",
        quality=request.quality,
        format=request.format,
        filename=request.filename,
        thumbnail=request.thumbnail,
        metadata=request.metadata,
        chapters=request.chapters,
        subtitles=request.subtitles,
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=str(request.url),
        job_type=job.job_type.value,
        message="Video download started",
        created_at=job.created_at.isoformat()
    )


@router.post("/download/audio", response_model=JobResponse)
async def download_audio(
    request: AudioDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Download audio only.

    Formats: mp3, m4a, flac, wav, aac, ogg
    """
    if not _validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid or blocked URL")

    job = await _create_job(
        db,
        str(request.url),
        DownloadType.AUDIO,
        {
            "format": request.format,
            "quality": request.quality,
            "filename": request.filename,
            "thumbnail": request.thumbnail,
            "metadata": request.metadata,
        }
    )

    background_tasks.add_task(
        _process_download,
        job.id,
        str(request.url),
        "audio",
        format=request.format,
        filename=request.filename,
        thumbnail=request.thumbnail,
        metadata=request.metadata,
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=str(request.url),
        job_type=job.job_type.value,
        message="Audio download started",
        created_at=job.created_at.isoformat()
    )


@router.post("/download/playlist", response_model=JobResponse)
async def download_playlist(
    request: PlaylistDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Download playlist.

    Options: quality, format, max_items, start_index, end_index
    """
    if not _validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid or blocked URL")

    job = await _create_job(
        db,
        str(request.url),
        DownloadType.PLAYLIST,
        {
            "format": request.format,
            "quality": request.quality,
            "filename": request.filename,
            "thumbnail": request.thumbnail,
            "metadata": request.metadata,
            "chapters": request.chapters,
            "subtitles": request.subtitles,
            "max_items": request.max_items,
        }
    )

    background_tasks.add_task(
        _process_download,
        job.id,
        str(request.url),
        "playlist",
        quality=request.quality,
        format=request.format,
        filename=request.filename,
        thumbnail=request.thumbnail,
        metadata=request.metadata,
        chapters=request.chapters,
        subtitles=request.subtitles,
        max_items=request.max_items,
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=str(request.url),
        job_type=job.job_type.value,
        message="Playlist download started",
        created_at=job.created_at.isoformat()
    )


@router.post("/download/custom", response_model=JobResponse)
async def download_custom(
    request: CustomDownloadRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Download with custom format string.

    Use format_string for custom yt-dlp format (e.g., 'bestvideo[height<=1080]+bestaudio')
    """
    if not _validate_url(str(request.url)):
        raise HTTPException(status_code=400, detail="Invalid or blocked URL")

    job = await _create_job(
        db,
        str(request.url),
        DownloadType.CUSTOM,
        {
            "format": request.format,
            "quality": request.quality,
            "filename": request.filename,
            "thumbnail": request.thumbnail,
            "metadata": request.metadata,
            "chapters": request.chapters,
            "subtitles": request.subtitles,
            "format_string": request.format_string,
        }
    )

    background_tasks.add_task(
        _process_download,
        job.id,
        str(request.url),
        "video",
        quality=request.quality,
        format=request.format,
        filename=request.filename,
        thumbnail=request.thumbnail,
        metadata=request.metadata,
        chapters=request.chapters,
        subtitles=request.subtitles,
        format_string=request.format_string,
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=str(request.url),
        job_type=job.job_type.value,
        message="Custom download started",
        created_at=job.created_at.isoformat()
    )


@router.get("/download/formats", response_model=FormatListResponse)
async def list_formats():
    """List available format presets."""
    from app.constants import VIDEO_QUALITY_PRESETS, AUDIO_FORMAT_PRESETS, OutputFormat

    return FormatListResponse(
        video_presets=VIDEO_QUALITY_PRESETS,
        audio_formats=list(AUDIO_FORMAT_PRESETS.keys()),
        supported_formats=[f.value for f in OutputFormat]
    )


@router.get("/download/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get download job status and information."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobStatusResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=job.url,
        job_type=job.job_type.value if job.job_type else None,
        title=job.title,
        description=job.description,
        thumbnail_url=job.thumbnail_url,
        uploader=job.uploader,
        duration=job.duration,
        format=job.video_format,
        quality=job.quality,
        output_format=job.output_format,
        file_path=job.file_path,
        file_size=job.file_size,
        file_name=job.file_name,
        progress=job.progress,
        speed=job.speed,
        eta=job.eta,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )


@router.delete("/download/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Cancel or delete a download job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status in [DownloadStatus.PENDING, DownloadStatus.PROCESSING]:
        job.status = DownloadStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        await db.commit()

    await db.delete(job)
    await db.commit()

    return {"success": True, "message": f"Job {job_id} deleted"}


@router.post("/download/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    request: RetryJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed download job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    result = await db.execute(select(Job).where(Job.id == job_uuid))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status != DownloadStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not in failed state (current: {job.status.value})"
        )

    job.status = DownloadStatus.PENDING
    job.error_message = None
    job.retries = 0
    job.max_retries = request.max_retries
    job.updated_at = datetime.utcnow()
    await db.commit()

    background_tasks.add_task(
        _process_download,
        job.id,
        str(job.url),
        job.job_type.value if job.job_type else "video",
    )

    return JobResponse(
        job_id=str(job.id),
        status=job.status.value,
        url=job.url,
        job_type=job.job_type.value if job.job_type else "video",
        message="Job retry started",
        created_at=job.updated_at.isoformat()
    )


@router.get("/download", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    job_type: Optional[str] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List download jobs with optional filters."""
    query = select(Job).order_by(Job.created_at.desc())

    if status:
        try:
            status_enum = DownloadStatus(status)
            query = query.where(Job.status == status_enum)
        except ValueError:
            pass

    if job_type:
        try:
            type_enum = DownloadType(job_type)
            query = query.where(Job.job_type == type_enum)
        except ValueError:
            pass

    total_result = await db.execute(query)
    total = len(total_result.scalars().all())

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    jobs = result.scalars().all()

    job_responses = [
        JobStatusResponse(
            job_id=str(job.id),
            status=job.status.value,
            url=job.url,
            job_type=job.job_type.value if job.job_type else None,
            title=job.title,
            file_name=job.file_name,
            file_size=job.file_size,
            progress=job.progress,
            created_at=job.created_at.isoformat() if job.created_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
        for job in jobs
    ]

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )