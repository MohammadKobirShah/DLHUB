"""
DLHUB - yt-dlp Service Wrapper
===============================
Production-grade yt-dlp integration with YouTube optimization.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import asyncio
import logging
import os
import subprocess
import json
import re
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.constants import (
    DownloadStatus,
    DownloadType,
    VIDEO_QUALITY_PRESETS,
    AUDIO_FORMAT_PRESETS,
    YT_DLP_USER_AGENT,
)
from app.exceptions import (
    InvalidURLException,
    URLBlockedException,
    DownloadFailedException,
    DownloadTimeoutException,
    FileTooLargeException,
    DurationTooLongException,
)
from app.utils.sanitizer import sanitize_filename

logger = logging.getLogger(__name__)


class YTDLPService:
    """yt-dlp service wrapper with YouTube optimization."""

    def __init__(self):
        self.download_dir = settings.DOWNLOAD_DIR
        self.temp_dir = settings.TEMP_DIR
        self.cookies_file = settings.COOKIES_FILE if os.path.exists(settings.COOKIES_FILE) else None

        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

        self._yt_dlp_path = self._find_yt_dlp()

    def _find_yt_dlp(self) -> str:
        """Find yt-dlp executable."""
        possible_paths = [
            "/usr/local/bin/yt-dlp",
            "/usr/bin/yt-dlp",
            "/opt/yt-dlp/yt-dlp",
            "yt-dlp",
        ]
        for path in possible_paths:
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found yt-dlp at: {path}")
                    return path
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        result = subprocess.run(
            ["which", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()

        raise RuntimeError("yt-dlp not found")

    def _build_base_options(self) -> List[str]:
        """Build base yt-dlp options."""
        opts = [
            "--no-warnings",
            "--no-check-certificate",
            "--no-color",
            f"--user-agent={YT_DLP_USER_AGENT}",
            f"--download-sections-strategy=download-sections-if-no-args",
        ]

        if self.cookies_file:
            opts.extend([f"--cookies={self.cookies_file}"])

        return opts

    def _get_format_string(self, download_type: str, quality: Optional[str] = None,
                          custom_format: Optional[str] = None) -> str:
        """Get format string based on download type and quality."""
        if custom_format:
            return custom_format

        if download_type == "audio":
            format_map = {
                "mp3": "bestaudio[ext=m4a]/bestaudio",
                "m4a": "bestaudio",
                "flac": "bestaudio[ext=flac]/bestaudio",
                "wav": "bestaudio",
                "aac": "bestaudio[ext=m4a]/bestaudio",
                "ogg": "bestaudio[ext=ogg]/bestaudio",
            }
            return format_map.get(settings.YTDLP_AUDIO_FORMAT, "bestaudio")

        if quality and quality in VIDEO_QUALITY_PRESETS:
            return VIDEO_QUALITY_PRESETS[quality]

        return settings.YTDLP_FORMAT

    def _get_output_template(self, filename: Optional[str] = None) -> str:
        """Get output template."""
        if filename:
            sanitized = sanitize_filename(filename)
            return os.path.join(self.download_dir, f"{sanitized}.%(ext)s")
        return os.path.join(self.download_dir, "%(title)s-%(id)s.%(ext)s")

    def _get_embed_options(self, request_params: Dict[str, Any]) -> List[str]:
        """Get embedding options based on request."""
        opts = []

        if request_params.get("thumbnail", True):
            opts.extend(["--embed-thumbnail"])

        if request_params.get("metadata", True):
            opts.extend(["--add-metadata", "--metadata-from_title=%(title)s"])

        if request_params.get("chapters", True):
            opts.extend(["--embed-chapters"])

        if request_params.get("subtitles", True):
            opts.extend([
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang",
                settings.YTDLP_SUBTITLE_LANGS,
                "--embed-subs",
            ])

        return opts

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract video information without downloading."""
        cmd = [
            self._yt_dlp_path,
            "--dump-json",
            "--no-download",
            "--no-playlist",
        ]
        cmd.extend(self._build_base_options())

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)

            if result.returncode != 0:
                error_msg = stderr.decode() or "Failed to extract video info"
                raise DownloadFailedException(error_msg)

            return json.loads(stdout.decode())

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Video info extraction timed out")
        except json.JSONDecodeError:
            raise DownloadFailedException("Invalid video info response")

    async def get_formats(self, url: str) -> List[Dict[str, Any]]:
        """Get available formats for a URL."""
        cmd = [
            self._yt_dlp_path,
            "--list-formats",
            "--no-download",
            "--no-playlist",
        ]
        cmd.extend(self._build_base_options())

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)

            formats = []
            for line in stdout.decode().split("\n"):
                if re.match(r"^\d+", line):
                    parts = line.split()
                    if len(parts) >= 4:
                        formats.append({
                            "format_id": parts[0],
                            "ext": parts[1],
                            "resolution": parts[2] if len(parts) > 2 else "unknown",
                            "note": " ".join(parts[3:]) if len(parts) > 3 else ""
                        })

            return formats

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Format listing timed out")
        except Exception as e:
            raise DownloadFailedException(f"Failed to list formats: {str(e)}")

    async def get_playlist_info(self, url: str) -> Dict[str, Any]:
        """Get playlist information."""
        cmd = [
            self._yt_dlp_path,
            "--dump-json",
            "--flat-playlist",
        ]
        cmd.extend(self._build_base_options())

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)

            if result.returncode != 0:
                error_msg = stderr.decode() or "Failed to extract playlist info"
                raise DownloadFailedException(error_msg)

            videos = []
            for line in stdout.decode().strip().split("\n"):
                if line.strip():
                    videos.append(json.loads(line))

            return {
                "video_count": len(videos),
                "videos": videos
            }

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Playlist info extraction timed out")
        except Exception as e:
            raise DownloadFailedException(f"Failed to get playlist info: {str(e)}")

    async def download(
        self,
        url: str,
        download_type: str = "video",
        quality: Optional[str] = None,
        output_format: Optional[str] = None,
        filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Download media from URL.

        Args:
            url: URL to download
            download_type: Type of download (video, audio, playlist)
            quality: Video quality preset
            output_format: Output file format
            filename: Custom filename
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with download result
        """
        logger.info(f"Starting download: {url} (type: {download_type})")

        output_template = self._get_output_template(filename)

        cmd = [
            self._yt_dlp_path,
            "--output",
            output_template,
            "--format",
            self._get_format_string(download_type, quality, kwargs.get("format_string")),
            "--merge-output-format",
            output_format or ("mp4" if download_type == "video" else "mp3"),
        ]

        cmd.extend(self._build_base_options())
        cmd.extend(self._get_embed_options(kwargs))

        cmd.extend([
            "--retries",
            str(settings.YTDLP_RETRIES),
            "--fragment-retries",
            str(settings.YTDLP_FRAGMENT_RETRIES),
            "--no-abort-on-error",
            "--continue-on-error",
        ])

        if download_type == "playlist":
            cmd.extend(["--no-playlist-items", str(kwargs.get("max_items", 100))])

        cmd.append(url)

        logger.debug(f"yt-dlp command: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=settings.WORKER_TIMEOUT
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise DownloadTimeoutException(f"Download timed out after {settings.WORKER_TIMEOUT}s")

            output = stdout.decode() + stderr.decode()
            logger.debug(f"yt-dlp output: {output}")

            if process.returncode != 0:
                if "HTTP Error 403" in output:
                    raise DownloadFailedException("Access forbidden - may require cookies")
                elif "HTTP Error 429" in output:
                    raise DownloadFailedException("Rate limited - try again later")
                elif "Video unavailable" in output:
                    raise DownloadFailedException("Video is unavailable")
                else:
                    raise DownloadFailedException(f"Download failed: {output[:500]}")

            output_files = list(Path(self.download_dir).glob("*"))
            output_files = [f for f in output_files if f.is_file()]

            if not output_files:
                raise DownloadFailedException("No output file generated")

            latest_file = max(output_files, key=lambda x: x.stat().st_mtime)

            file_info = {
                "file_path": str(latest_file),
                "file_name": latest_file.name,
                "file_size": latest_file.stat().st_size,
                "extension": latest_file.suffix[1:] if latest_file.suffix else None,
            }

            logger.info(f"Download completed: {file_info['file_name']}")
            return file_info

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Download operation timed out")
        except DownloadFailedException:
            raise
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            raise DownloadFailedException(f"Download failed: {str(e)}")

    async def download_subtitles(self, url: str, languages: Optional[List[str]] = None) -> Dict[str, Any]:
        """Download only subtitles."""
        languages = languages or ["en"]

        output_template = os.path.join(self.download_dir, "%(title)s-%(id)s.%(ext)s")

        cmd = [
            self._yt_dlp_path,
            "--output",
            output_template,
            "--write-subs",
            "--write-auto-subs",
            "--sub-lang",
            ",".join(languages),
            "--skip-download",
            "--no-playlist",
        ]
        cmd.extend(self._build_base_options())
        cmd.append(url)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=300)

            if result.returncode != 0:
                raise DownloadFailedException(f"Subtitle download failed: {stderr.decode()}")

            return {"status": "completed", "message": "Subtitles downloaded"}

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Subtitle download timed out")

    async def download_thumbnail(self, url: str) -> Dict[str, Any]:
        """Download only thumbnail."""
        cmd = [
            self._yt_dlp_path,
            "--output",
            os.path.join(self.download_dir, "%(title)s-%(id)s.%(ext)s"),
            "--write-thumbnail",
            "--skip-download",
            "--no-playlist",
        ]
        cmd.extend(self._build_base_options())
        cmd.append(url)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=60)

            if result.returncode != 0:
                raise DownloadFailedException(f"Thumbnail download failed: {stderr.decode()}")

            return {"status": "completed", "message": "Thumbnail downloaded"}

        except asyncio.TimeoutError:
            raise DownloadTimeoutException("Thumbnail download timed out")

    def get_version(self) -> str:
        """Get yt-dlp version."""
        try:
            result = subprocess.run(
                [self._yt_dlp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get yt-dlp version: {e}")
            return "unknown"

    def update(self) -> Dict[str, str]:
        """Update yt-dlp to latest version."""
        logger.info("Updating yt-dlp...")
        try:
            result = subprocess.run(
                [self._yt_dlp_path, "-U"],
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            logger.error(f"Failed to update yt-dlp: {e}")
            return {"success": False, "error": str(e)}


yt_dlp_service = YTDLPService()