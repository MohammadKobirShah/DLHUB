"""
DLHUB - Response Schemas
=========================
Pydantic models for API response validation.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    """Job creation response."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    url: str = Field(..., description="Download URL")
    job_type: str = Field(..., description="Type of download")
    message: str = Field(..., description="Status message")
    created_at: str = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Job status response."""

    job_id: str
    status: str
    url: str
    job_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    uploader: Optional[str] = None
    duration: Optional[int] = None
    format: Optional[str] = None
    quality: Optional[str] = None
    output_format: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    file_name: Optional[str] = None
    progress: Optional[float] = None
    speed: Optional[str] = None
    eta: Optional[int] = None
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Job list response with pagination."""

    jobs: List[JobStatusResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FileResponse(BaseModel):
    """File information response."""

    id: str = Field(..., description="File unique identifier")
    job_id: Optional[str] = None
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    extension: Optional[str] = None
    is_video: Optional[bool] = None
    is_audio: Optional[bool] = None
    title: Optional[str] = None
    uploader: Optional[str] = None
    duration: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    downloads: Optional[int] = None
    created_at: Optional[str] = None


class FileListResponse(BaseModel):
    """File list response with pagination."""

    files: List[FileResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SystemStatsResponse(BaseModel):
    """System statistics response."""

    total_jobs: int
    pending_jobs: int
    processing_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int
    total_downloads: int
    total_size: int
    active_workers: int
    queue_size: int
    uptime: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    database: Optional[str] = None
    redis: Optional[str] = None
    storage: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class VersionResponse(BaseModel):
    """Version information response."""

    app_name: str
    version: str
    api_version: str
    yt_dlp_version: Optional[str] = None
    ffmpeg_version: Optional[str] = None
    python_version: str
    build_date: Optional[str] = None


class StorageResponse(BaseModel):
    """Storage information response."""

    total_space: int
    used_space: int
    free_space: int
    usage_percent: float
    download_count: int
    largest_file: Optional[Dict[str, Any]] = None


class FormatListResponse(BaseModel):
    """Available formats list response."""

    video_presets: Dict[str, str]
    audio_formats: List[str]
    supported_formats: List[str]


class DownloadProgressResponse(BaseModel):
    """Download progress response."""

    job_id: str
    status: str
    progress: float
    speed: Optional[str] = None
    eta: Optional[int] = None
    downloaded_size: Optional[int] = None
    total_size: Optional[int] = None
    fragment: Optional[int] = None
    total_fragments: Optional[int] = None


class QueueStatusResponse(BaseModel):
    """Queue status response."""

    queue_size: int
    pending_jobs: int
    processing_jobs: int
    worker_count: int
    is_paused: bool


class YouTubeVideoInfoResponse(BaseModel):
    """YouTube video information response."""

    id: str
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    uploader: Optional[str] = None
    uploader_url: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    channel_id: Optional[str] = None
    channel_url: Optional[str] = None
    tags: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    subtitles: Optional[Dict[str, str]] = None
    chapters: Optional[List[Dict[str, Any]]] = None
    available_formats: Optional[List[Dict[str, Any]]] = None


class YouTubePlaylistInfoResponse(BaseModel):
    """YouTube playlist information response."""

    id: str
    title: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None
    video_count: int
    length_seconds: Optional[int] = None
    videos: Optional[List[Dict[str, Any]]] = None


class YouTubeChannelInfoResponse(BaseModel):
    """YouTube channel information response."""

    id: str
    name: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    banner: Optional[str] = None
    subscriber_count: Optional[int] = None
    video_count: Optional[int] = None
    total_views: Optional[int] = None
    created_date: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None