"""
DLHUB - Files Router
====================
File management and serving endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import os
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.schemas.response import FileResponse as FileSchemaResponse
from app.schemas.response import FileListResponse
from app.utils.sanitizer import sanitize_path

router = APIRouter()


def get_file_info(file_path: Path) -> dict:
    """Get file information."""
    stat = file_path.stat()
    return {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "file_size": stat.st_size,
        "extension": file_path.suffix[1:] if file_path.suffix else None,
        "created_at": stat.st_ctime,
        "modified_at": stat.st_mtime,
    }


@router.get("/files", response_model=FileListResponse)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by filename"),
    extension: Optional[str] = Query(None, description="Filter by extension"),
):
    """
    List all downloaded files.
    """
    download_path = Path(settings.DOWNLOAD_DIR)

    if not download_path.exists():
        return FileListResponse(files=[], total=0, page=1, page_size=page_size, pages=0)

    try:
        all_files = [f for f in download_path.iterdir() if f.is_file()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

    if search:
        all_files = [f for f in all_files if search.lower() in f.name.lower()]

    if extension:
        all_files = [f for f in all_files if f.suffix[1:].lower() == extension.lower()]

    total = len(all_files)
    pages = (total + page_size - 1) // page_size

    start = (page - 1) * page_size
    end = start + page_size
    paginated_files = all_files[start:end]

    files = []
    for f in paginated_files:
        try:
            info = get_file_info(f)
            files.append(FileSchemaResponse(
                id=f.stem,
                file_name=info["file_name"],
                file_path=info["file_path"],
                file_size=info["file_size"],
                extension=info["extension"],
                created_at=str(info["created_at"]),
            ))
        except Exception:
            continue

    return FileListResponse(
        files=files,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.get("/files/{filename}")
async def get_file(
    filename: str,
    download: bool = Query(False, description="Force download instead of stream"),
):
    """
    Get or download a file.

    Set download=true to force file download instead of streaming.
    """
    download_path = Path(settings.DOWNLOAD_DIR)

    file_path = download_path / filename

    try:
        safe_path = sanitize_path(str(file_path), str(download_path))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    if not os.path.isfile(safe_path):
        raise HTTPException(status_code=400, detail="Not a file")

    if download:
        return FileResponse(
            path=safe_path,
            filename=filename,
            media_type="application/octet-stream"
        )

    ext = Path(safe_path).suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".flac": "audio/flac",
        ".wav": "audio/wav",
        ".json": "application/json",
        ".txt": "text/plain",
        ".srt": "text/plain",
        ".vtt": "text/vtt",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=safe_path,
        media_type=media_type,
        filename=filename
    )


@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """
    Delete a downloaded file.
    """
    download_path = Path(settings.DOWNLOAD_DIR)
    file_path = download_path / filename

    try:
        safe_path = sanitize_path(str(file_path), str(download_path))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        os.remove(safe_path)
        return {"success": True, "message": f"File deleted: {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")


@router.get("/files/{filename}/stream")
async def stream_file(
    filename: str,
    start: int = Query(0, description="Start byte"),
    end: Optional[int] = Query(None, description="End byte"),
):
    """
    Stream file with byte range support.

    Supports HTTP Range requests for video streaming.
    """
    download_path = Path(settings.DOWNLOAD_DIR)
    file_path = download_path / filename

    try:
        safe_path = sanitize_path(str(file_path), str(download_path))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    file_size = os.path.getsize(safe_path)

    if end is None or end > file_size:
        end = file_size - 1

    def iter_file(start: int, end: int):
        with open(safe_path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk_size = min(1024 * 1024, remaining)
                data = f.read(chunk_size)
                if not data:
                    break
                remaining -= chunk_size
                yield data

    ext = Path(safe_path).suffix.lower()
    media_types = {
        ".mp4": "video/mp4",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(end - start + 1),
    }

    return StreamingResponse(
        iter_file(start, end),
        media_type=media_type,
        status_code=206,
        headers=headers
    )


@router.post("/files/cleanup")
async def cleanup_files(
    older_than_days: int = Query(7, ge=1, description="Delete files older than N days"),
    dry_run: bool = Query(False, description="Preview files to be deleted without deleting"),
):
    """
    Cleanup old files from download directory.
    """
    import time

    download_path = Path(settings.DOWNLOAD_DIR)

    if not download_path.exists():
        raise HTTPException(status_code=404, detail="Download directory not found")

    current_time = time.time()
    cutoff_time = current_time - (older_than_days * 86400)

    files_to_delete = []
    for f in download_path.iterdir():
        if f.is_file() and f.stat().st_mtime < cutoff_time:
            files_to_delete.append(f)

    if dry_run:
        return {
            "dry_run": True,
            "files_count": len(files_to_delete),
            "files": [f.name for f in files_to_delete]
        }

    deleted_count = 0
    for f in files_to_delete:
        try:
            f.unlink()
            deleted_count += 1
        except Exception:
            continue

    return {
        "deleted_count": deleted_count,
        "total_files_scanned": len(files_to_delete)
    }