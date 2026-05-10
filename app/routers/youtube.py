"""
DLHUB - YouTube Router
======================
YouTube info and metadata endpoints.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query

from app.services.yt_dlp_service import yt_dlp_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/youtube/video/{video_id}")
async def get_video_info(video_id: str):
    """Get video information."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        return {
            "id": info.get("id"),
            "title": info.get("title"),
            "description": info.get("description"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "uploader_url": info.get("uploader_url"),
            "upload_date": info.get("upload_date"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "channel_id": info.get("channel_id"),
            "channel_url": info.get("channel_url"),
            "tags": info.get("tags", []),
            "categories": info.get("categories", []),
            "extractor": info.get("extractor"),
            "extractor_version": info.get("extractor_version"),
        }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/playlist/{playlist_id}")
async def get_playlist_info(playlist_id: str):
    """Get playlist information."""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"

    try:
        result = await yt_dlp_service.get_playlist_info(url)

        videos = result.get("videos", [])
        video_list = []
        for v in videos[:50]:
            video_list.append({
                "id": v.get("id"),
                "title": v.get("title"),
                "duration": v.get("duration"),
                "uploader": v.get("uploader"),
                "thumbnail": v.get("thumbnail"),
            })

        return {
            "id": playlist_id,
            "video_count": result.get("video_count"),
            "videos": video_list,
        }
    except Exception as e:
        logger.error(f"Failed to get playlist info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/channel/{channel_id}")
async def get_channel_info(channel_id: str):
    """Get channel information."""
    url = f"https://www.youtube.com/channel/{channel_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        return {
            "id": channel_id,
            "name": info.get("channel"),
            "description": info.get("description"),
            "thumbnail": info.get("thumbnail"),
            "banner": info.get("channel_banner"),
            "subscriber_count": info.get("channel_follower_count"),
            "view_count": info.get("channel_view_count"),
            "video_count": info.get("playlist_count"),
        }
    except Exception as e:
        logger.error(f"Failed to get channel info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/captions/{video_id}")
async def get_captions(video_id: str):
    """Get available captions for video."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        subtitles = info.get("subtitles", {})
        automatic_captions = info.get("automatic_captions", {})

        all_captions = {}

        for lang, data in subtitles.items():
            all_captions[lang] = {
                "type": "manual",
                "formats": [f.get("ext") for f in data] if isinstance(data, list) else []
            }

        for lang, data in automatic_captions.items():
            if lang not in all_captions:
                all_captions[lang] = {
                    "type": "automatic",
                    "formats": [f.get("ext") for f in data] if isinstance(data, list) else []
                }

        return {
            "video_id": video_id,
            "captions": all_captions
        }
    except Exception as e:
        logger.error(f"Failed to get captions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/chapters/{video_id}")
async def get_chapters(video_id: str):
    """Get video chapters."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        chapters = info.get("chapters", [])
        if not chapters and info.get("tags"):
            chapters = info.get("requested_chapters", [])

        chapter_list = []
        for ch in chapters:
            chapter_list.append({
                "title": ch.get("title", "Chapter"),
                "start_time": ch.get("start_time"),
                "end_time": ch.get("end_time"),
            })

        return {
            "video_id": video_id,
            "chapters": chapter_list
        }
    except Exception as e:
        logger.error(f"Failed to get chapters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/search")
async def search_youtube(
    query: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=50)
):
    """Search YouTube."""
    import subprocess
    import json

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print", "%(id)s|%(title)s|%(duration)s|%(thumbnail)s",
                f"ytsearch{limit}:{query}"
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        results = []
        for line in result.stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    results.append({
                        "id": parts[0].strip(),
                        "title": parts[1].strip(),
                        "duration": parts[2].strip() if len(parts) > 2 else None,
                        "thumbnail": parts[3].strip() if len(parts) > 3 else None,
                    })

        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"YouTube search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/formats/{video_id}")
async def get_available_formats(video_id: str):
    """Get available formats for video."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        formats = await yt_dlp_service.get_formats(url)

        video_formats = []
        audio_formats = []
        video_audio_combo = []

        for f in formats:
            fmt_id = f.get("format_id", "")
            ext = f.get("ext", "")
            resolution = f.get("resolution", "")

            if "video" in fmt_id or resolution:
                video_formats.append(f)
            elif "audio" in fmt_id:
                audio_formats.append(f)
            else:
                video_audio_combo.append(f)

        return {
            "video_id": video_id,
            "video_formats": video_formats[:30],
            "audio_formats": audio_formats[:15],
            "combined_formats": video_audio_combo[:30],
        }
    except Exception as e:
        logger.error(f"Failed to get formats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/live/{video_id}")
async def get_live_info(video_id: str):
    """Get live stream information."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        is_live = info.get("is_live", False)
        is_upcoming = info.get("is_upcoming", False)
        was_live = info.get("was_live", False)

        return {
            "video_id": video_id,
            "is_live": is_live,
            "is_upcoming": is_upcoming,
            "was_live": was_live,
            "live_start_time": info.get("live_start_time"),
            "live_broadcast_content": info.get("live_broadcast_content"),
        }
    except Exception as e:
        logger.error(f"Failed to get live info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/trending")
async def get_trending(
    region: str = Query("US", description="Region code"),
    category: Optional[str] = Query(None, description="Category")
):
    """Get trending videos."""
    import subprocess

    try:
        url = f"https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--print", "%(id)s|%(title)s", "ytsearch20:trending"],
            capture_output=True,
            text=True,
            timeout=60
        )

        videos = []
        for line in result.stdout.strip().split("\n")[:20]:
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    videos.append({
                        "id": parts[0].strip(),
                        "title": parts[1].strip()
                    })

        return {
            "region": region,
            "videos": videos,
            "count": len(videos)
        }
    except Exception as e:
        logger.error(f"Failed to get trending: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/youtube/related/{video_id}")
async def get_related_videos(video_id: str):
    """Get related videos."""
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        info = await yt_dlp_service.get_video_info(url)

        related = info.get("related_videos", [])[:20]

        videos = []
        for r in related:
            videos.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "duration": r.get("duration"),
                "uploader": r.get("uploader"),
                "thumbnail": r.get("thumbnail"),
            })

        return {
            "video_id": video_id,
            "related_videos": videos
        }
    except Exception as e:
        logger.error(f"Failed to get related videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))