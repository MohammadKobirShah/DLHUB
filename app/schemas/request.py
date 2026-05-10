"""
DLHUB - Request Schemas
========================
Pydantic models for API request validation.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, validator


class BaseDownloadRequest(BaseModel):
    """Base download request with common fields."""

    url: HttpUrl = Field(..., description="URL to download")
    quality: Optional[str] = Field(None, description="Video quality (best, 2160p, 1440p, 1080p, 720p, 480p, 360p, 240p, 144p)")
    format: Optional[str] = Field(None, description="Output format (mp4, mkv, webm)")
    filename: Optional[str] = Field(None, description="Custom filename template")
    subtitles: Optional[bool] = Field(True, description="Download subtitles")
    thumbnail: Optional[bool] = Field(True, description="Embed thumbnail")
    metadata: Optional[bool] = Field(True, description="Add metadata")
    chapters: Optional[bool] = Field(True, description="Embed chapters")
    cookies: Optional[bool] = Field(False, description="Use cookies file")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "quality": "best",
                "format": "mp4",
                "subtitles": True,
                "thumbnail": True,
                "metadata": True
            }
        }


class VideoDownloadRequest(BaseDownloadRequest):
    """Video download request."""

    quality: Optional[str] = Field("best", description="Video quality preset")
    format: Optional[str] = Field("mp4", description="Output format", pattern=r"^(mp4|mkv|webm)$")

    @validator("quality")
    def validate_quality(cls, v):
        valid_qualities = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
        if v and v not in valid_qualities:
            raise ValueError(f"Quality must be one of: {', '.join(valid_qualities)}")
        return v


class AudioDownloadRequest(BaseDownloadRequest):
    """Audio download request."""

    format: Optional[str] = Field("mp3", description="Audio format", pattern=r"^(mp3|m4a|flac|wav|aac|ogg)$")
    bitrate: Optional[str] = Field("192k", description="Audio bitrate")

    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["mp3", "m4a", "flac", "wav", "aac", "ogg"]
        if v and v not in valid_formats:
            raise ValueError(f"Format must be one of: {', '.join(valid_formats)}")
        return v


class PlaylistDownloadRequest(BaseDownloadRequest):
    """Playlist download request."""

    quality: Optional[str] = Field("best", description="Video quality")
    format: Optional[str] = Field("mp4", description="Output format")
    start_index: Optional[int] = Field(1, ge=1, description="Start downloading from this position")
    end_index: Optional[int] = Field(None, ge=1, description="End downloading at this position")
    max_items: Optional[int] = Field(100, ge=1, le=500, description="Maximum items to download")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.youtube.com/playlist?list=PL123456789",
                "quality": "720p",
                "format": "mp4",
                "max_items": 50
            }
        }


class CustomDownloadRequest(BaseDownloadRequest):
    """Custom format download request."""

    format_string: Optional[str] = Field(
        None,
        description="Custom yt-dlp format string (e.g., 'bestvideo[height<=1080]+bestaudio')"
    )
    merge_output_format: Optional[str] = Field("mp4", description="Format for merged output")
    extra_args: Optional[List[str]] = Field(None, description="Extra yt-dlp arguments")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "format_string": "bestvideo[height<=720]+bestaudio",
                "merge_output_format": "mkv"
            }
        }


class RetryJobRequest(BaseModel):
    """Retry failed job request."""

    max_retries: Optional[int] = Field(3, ge=1, le=10, description="Maximum retry attempts")

    class Config:
        schema_extra = {
            "example": {
                "max_retries": 5
            }
        }


class MediaTranscodeRequest(BaseModel):
    """Media transcoding request."""

    file_path: str = Field(..., description="Path to media file")
    output_format: str = Field(..., description="Target format", pattern=r"^(mp4|mkv|webm|mp3|m4a)$")
    video_codec: Optional[str] = Field(None, description="Video codec (h264, h265, vp9)")
    audio_codec: Optional[str] = Field(None, description="Audio codec (aac, mp3, copy)")
    video_bitrate: Optional[str] = Field(None, description="Video bitrate")
    audio_bitrate: Optional[str] = Field(None, description="Audio bitrate")
    resolution: Optional[str] = Field(None, description="Target resolution (1920x1080)")
    speed_preset: Optional[str] = Field("medium", description="Encoding speed (ultrafast, fast, medium, slow)")
    crf: Optional[int] = Field(23, ge=0, le=51, description="CRF value for quality")

    class Config:
        schema_extra = {
            "example": {
                "file_path": "/downloads/video.mp4",
                "output_format": "mp4",
                "video_codec": "h264",
                "audio_codec": "aac",
                "resolution": "1920x1080",
                "crf": 23
            }
        }


class MediaExtractAudioRequest(BaseModel):
    """Extract audio from video request."""

    file_path: str = Field(..., description="Path to video file")
    output_format: str = Field("mp3", description="Audio output format", pattern=r"^(mp3|m4a|flac|wav|aac|ogg)$")
    audio_bitrate: Optional[str] = Field("192k", description="Audio bitrate")
    audio_quality: Optional[int] = Field(2, ge=0, le=9, description="VBR quality (0=best, 9=worst)")

    class Config:
        schema_extra = {
            "example": {
                "file_path": "/downloads/video.mp4",
                "output_format": "mp3",
                "audio_bitrate": "320k"
            }
        }


class MediaMergeRequest(BaseModel):
    """Merge multiple media files request."""

    input_files: List[str] = Field(..., min_items=2, description="List of input files to merge")
    output_filename: str = Field(..., description="Output filename")
    output_format: str = Field("mp4", description="Output format")


class MediaTrimRequest(BaseModel):
    """Trim media file request."""

    file_path: str = Field(..., description="Path to media file")
    start_time: str = Field(..., description="Start time (seconds or HH:MM:SS)")
    end_time: str = Field(..., description="End time (seconds or HH:MM:SS)")
    output_filename: Optional[str] = Field(None, description="Output filename")


class MediaNormalizeRequest(BaseModel):
    """Audio normalization request."""

    file_path: str = Field(..., description="Path to audio/video file")
    target_loudness: Optional[str] = Field("-16", description="Target loudness LUFS")
    target_peak: Optional[str] = Field("-1.5", description="Target peak dB")
    loudness_range: Optional[str] = Field("11", description="Loudness range LU")


class QueueAddRequest(BaseModel):
    """Add job to queue request."""

    url: HttpUrl = Field(..., description="URL to queue")
    job_type: str = Field("video", description="Type of job (video, audio, playlist)")
    priority: Optional[int] = Field(1, ge=0, le=10, description="Job priority (0=lowest, 10=highest)")
    schedule_time: Optional[str] = Field(None, description="ISO datetime to schedule job")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class WebhookConfigRequest(BaseModel):
    """Configure webhook request."""

    url: HttpUrl = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to trigger webhook")
    secret: Optional[str] = Field(None, description="Webhook secret for signing")
    enabled: bool = Field(True, description="Enable/disable webhook")


class CookieUploadRequest(BaseModel):
    """Upload cookies file request."""

    cookies_file: str = Field(..., description="Path to cookies file (netscape format)")