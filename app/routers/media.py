"""
DLHUB - Media Router
====================
Media processing endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
import uuid
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.request import (
    MediaTranscodeRequest,
    MediaExtractAudioRequest,
    MediaMergeRequest,
    MediaTrimRequest,
    MediaNormalizeRequest,
)
from app.services.ffmpeg_service import ffmpeg_service

logger = logging.getLogger(__name__)

router = APIRouter()


def get_output_path(filename: str, prefix: str = "") -> str:
    """Generate output file path."""
    download_dir = Path(settings.DOWNLOAD_DIR)
    if prefix:
        filename = f"{prefix}_{filename}"
    return str(download_dir / filename)


@router.post("/media/transcode")
async def transcode_media(
    request: MediaTranscodeRequest,
    background_tasks: BackgroundTasks
):
    """Transcode media to different format."""
    input_path = Path(settings.DOWNLOAD_DIR) / request.file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")

    output_filename = f"{input_path.stem}_transcoded.{request.output_format}"
    output_path = get_output_path(output_filename)

    task = background_tasks.add_task(
        ffmpeg_service.transcode,
        str(input_path),
        output_path,
        request.video_codec or "libx264",
        request.audio_codec or "aac",
        request.video_bitrate,
        request.audio_bitrate or "192k",
        request.resolution,
        request.crf or 23,
        request.speed_preset or "medium"
    )

    return {
        "job_id": str(uuid.uuid4()),
        "input": str(input_path),
        "output": output_path,
        "status": "processing"
    }


@router.post("/media/extract-audio")
async def extract_audio(
    request: MediaExtractAudioRequest,
    background_tasks: BackgroundTasks
):
    """Extract audio from video."""
    input_path = Path(settings.DOWNLOAD_DIR) / request.file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")

    output_filename = f"{input_path.stem}.{request.output_format}"
    output_path = get_output_path(output_filename, "audio")

    background_tasks.add_task(
        ffmpeg_service.extract_audio,
        str(input_path),
        output_path,
        request.output_format,
        request.audio_bitrate or "192k"
    )

    return {
        "job_id": str(uuid.uuid4()),
        "input": str(input_path),
        "output": output_path,
        "status": "processing"
    }


@router.post("/media/merge")
async def merge_media(
    request: MediaMergeRequest,
    background_tasks: BackgroundTasks
):
    """Merge multiple media files."""
    input_files = []
    for f in request.input_files:
        fp = Path(settings.DOWNLOAD_DIR) / f
        if not fp.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {f}")
        input_files.append(str(fp))

    output_filename = f"{request.output_filename}.{request.output_format}"
    output_path = get_output_path(output_filename, "merged")

    background_tasks.add_task(
        ffmpeg_service.merge_videos,
        input_files,
        output_path,
        "concat"
    )

    return {
        "job_id": str(uuid.uuid4()),
        "inputs": request.input_files,
        "output": output_path,
        "status": "processing"
    }


@router.post("/media/trim")
async def trim_media(
    request: MediaTrimRequest,
    background_tasks: BackgroundTasks
):
    """Trim media file."""
    input_path = Path(settings.DOWNLOAD_DIR) / request.file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")

    output_filename = request.output_filename or f"{input_path.stem}_trimmed{input_path.suffix}"
    output_path = get_output_path(output_filename)

    background_tasks.add_task(
        ffmpeg_service.trim_media,
        str(input_path),
        output_path,
        request.start_time,
        request.end_time
    )

    return {
        "job_id": str(uuid.uuid4()),
        "input": str(input_path),
        "output": output_path,
        "start": request.start_time,
        "end": request.end_time,
        "status": "processing"
    }


@router.post("/media/normalize")
async def normalize_audio(
    request: MediaNormalizeRequest,
    background_tasks: BackgroundTasks
):
    """Normalize audio loudness."""
    input_path = Path(settings.DOWNLOAD_DIR) / request.file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Input file not found")

    output_filename = f"{input_path.stem}_normalized{input_path.suffix}"
    output_path = get_output_path(output_filename, "normalized")

    background_tasks.add_task(
        ffmpeg_service.normalize_audio,
        str(input_path),
        output_path,
        request.target_loudness or "-16",
        request.target_peak or "-1.5",
        request.loudness_range or "11"
    )

    return {
        "job_id": str(uuid.uuid4()),
        "input": str(input_path),
        "output": output_path,
        "status": "processing"
    }


@router.post("/media/waveform")
async def generate_waveform(
    file_path: str = Query(..., description="Path to audio file"),
    width: int = Query(800, ge=100, le=2000),
    height: int = Query(200, ge=50, le=500)
):
    """Generate audio waveform image."""
    input_path = Path(settings.DOWNLOAD_DIR) / file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    output_filename = f"{input_path.stem}_waveform.png"
    output_path = get_output_path(output_filename, "waveform")

    result = await ffmpeg_service.generate_waveform(
        str(input_path),
        output_path,
        width,
        height
    )

    if result.get("success"):
        return {
            "success": True,
            "output_path": result["output_path"],
            "download_url": f"/api/v1/files/{Path(result['output_path']).name}"
        }

    raise HTTPException(status_code=500, detail=result.get("error", "Waveform generation failed"))


@router.post("/media/preview")
async def generate_preview(
    file_path: str = Query(..., description="Path to video file"),
    duration: int = Query(10, ge=1, le=60),
    width: int = Query(480, ge=160, le=1920),
    start_time: str = Query("0")
):
    """Generate video preview clip."""
    input_path = Path(settings.DOWNLOAD_DIR) / file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    output_filename = f"{input_path.stem}_preview.mp4"
    output_path = get_output_path(output_filename, "preview")

    result = await ffmpeg_service.generate_preview(
        str(input_path),
        output_path,
        duration,
        width,
        start_time
    )

    if result.get("success"):
        return {
            "success": True,
            "output_path": result["output_path"],
            "download_url": f"/api/v1/files/{Path(result['output_path']).name}"
        }

    raise HTTPException(status_code=500, detail=result.get("error", "Preview generation failed"))


@router.post("/media/gif")
async def create_gif(
    file_path: str = Query(..., description="Path to video file"),
    duration: int = Query(5, ge=1, le=30),
    width: int = Query(320, ge=100, le=800),
    start_time: str = Query("0")
):
    """Create GIF from video."""
    input_path = Path(settings.DOWNLOAD_DIR) / file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    output_filename = f"{input_path.stem}.gif"
    output_path = get_output_path(output_filename, "gif")

    result = await ffmpeg_service.create_gif(
        str(input_path),
        output_path,
        start_time,
        duration,
        width
    )

    if result.get("success"):
        return {
            "success": True,
            "output_path": result["output_path"],
            "download_url": f"/api/v1/files/{Path(result['output_path']).name}"
        }

    raise HTTPException(status_code=500, detail=result.get("error", "GIF creation failed"))


@router.post("/media/screenshot")
async def take_screenshot(
    file_path: str = Query(..., description="Path to video file"),
    timestamp: str = Query("00:00:01")
):
    """Take screenshot at specific timestamp."""
    input_path = Path(settings.DOWNLOAD_DIR) / file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    output_filename = f"{input_path.stem}_screenshot.jpg"
    output_path = get_output_path(output_filename, "screenshot")

    result = await ffmpeg_service.take_screenshot(
        str(input_path),
        output_path,
        timestamp
    )

    if result.get("success"):
        return {
            "success": True,
            "output_path": result["output_path"],
            "download_url": f"/api/v1/files/{Path(result['output_path']).name}"
        }

    raise HTTPException(status_code=500, detail=result.get("error", "Screenshot failed"))


@router.get("/media/info")
async def get_media_info(
    file_path: str = Query(..., description="Path to media file")
):
    """Get media file information."""
    input_path = Path(settings.DOWNLOAD_DIR) / file_path

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    info = await ffmpeg_service.get_media_info(str(input_path))

    if info:
        return info

    raise HTTPException(status_code=500, detail="Failed to get media info")


@router.get("/media/formats")
async def list_supported_formats():
    """List supported media formats."""
    return {
        "video_codecs": ["libx264", "libx265", "libvpx", "libvpx-vp9"],
        "audio_codecs": ["aac", "libmp3lame", "flac", "libvorbis", "pcm_s16le"],
        "containers": ["mp4", "mkv", "webm", "avi", "mov"],
        "audio_formats": ["mp3", "m4a", "flac", "wav", "aac", "ogg"],
        "presets": ["ultrafast", "fast", "medium", "slow", "veryslow"]
    }