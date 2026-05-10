"""
DLHUB - FFmpeg Service
=======================
Media processing with FFmpeg.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import asyncio
import logging
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


class FFmpegService:
    """FFmpeg media processing service."""

    def __init__(self):
        self.timeout = settings.FFMPEG_TIMEOUT
        self.threads = settings.FFMPEG_THREADS

    def _run_ffmpeg(self, args: List[str], timeout: int = None) -> Tuple[int, str, str]:
        """Run ffmpeg command."""
        timeout = timeout or self.timeout
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg operation timed out")
            return -1, "", "Operation timed out"
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return -1, "", str(e)

    async def get_media_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get media file information."""
        args = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            if proc.returncode == 0:
                return json.loads(stdout.decode())
            return None
        except Exception as e:
            logger.error(f"Failed to get media info: {e}")
            return None

    async def transcode(
        self,
        input_path: str,
        output_path: str,
        video_codec: str = "libx264",
        audio_codec: str = "aac",
        video_bitrate: Optional[str] = None,
        audio_bitrate: str = "192k",
        resolution: Optional[str] = None,
        crf: int = 23,
        preset: str = "medium"
    ) -> Dict[str, Any]:
        """Transcode media file."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", video_codec,
            "-preset", preset,
            "-crf", str(crf),
            "-c:a", audio_codec,
            "-b:a", audio_bitrate,
            "-threads", str(self.threads),
        ]

        if video_bitrate:
            args.extend(["-b:v", video_bitrate])

        if resolution:
            args.extend(["-vf", f"scale={resolution.replace('x', ':')}"])

        args.extend([
            "-movflags", "+faststart",
            "-y",
            output_path
        ])

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Transcoding completed"
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode()[:500]
                }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Transcoding timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def extract_audio(
        self,
        input_path: str,
        output_path: str,
        format: str = "mp3",
        bitrate: str = "192k"
    ) -> Dict[str, Any]:
        """Extract audio from video."""
        codec_map = {
            "mp3": "libmp3lame",
            "aac": "aac",
            "flac": "flac",
            "wav": "pcm_s16le",
            "ogg": "libvorbis",
        }

        codec = codec_map.get(format, "libmp3lame")

        args = [
            "ffmpeg",
            "-i", input_path,
            "-vn",
            "-c:a", codec,
            "-b:a", bitrate,
            "-threads", str(self.threads),
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {
                    "success": True,
                    "output_path": output_path,
                    "message": "Audio extraction completed"
                }
            return {"success": False, "error": stderr.decode()[:500]}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Audio extraction timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def merge_videos(
        self,
        input_files: List[str],
        output_path: str,
        method: str = "concat"
    ) -> Dict[str, Any]:
        """Merge multiple video files."""
        if method == "concat":
            temp_list = Path(output_path).parent / "concat_list.txt"
            with open(temp_list, "w") as f:
                for file in input_files:
                    f.write(f"file '{file}'\n")

            args = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(temp_list),
                "-c", "copy",
                "-threads", str(self.threads),
                "-y",
                output_path
            ]

            try:
                loop = asyncio.get_event_loop()
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

                temp_list.unlink(missing_ok=True)

                if proc.returncode == 0:
                    return {"success": True, "output_path": output_path}
                return {"success": False, "error": stderr.decode()[:500]}
            except Exception as e:
                temp_list.unlink(missing_ok=True)
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Unsupported merge method"}

    async def trim_media(
        self,
        input_path: str,
        output_path: str,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """Trim media file."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-ss", start_time,
            "-to", end_time,
            "-c", "copy",
            "-threads", str(self.threads),
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Trim operation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def normalize_audio(
        self,
        input_path: str,
        output_path: str,
        target_loudness: str = "-16",
        target_peak: str = "-1.5",
        loudness_range: str = "11"
    ) -> Dict[str, Any]:
        """Normalize audio loudness."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-af", f"loudnorm=I={target_loudness}:TP={target_peak}:LRA={loudness_range}",
            "-c:a", "aac",
            "-b:a", "192k",
            "-threads", str(self.threads),
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Normalization timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_waveform(
        self,
        input_path: str,
        output_path: str,
        width: int = 800,
        height: int = 200,
        bgcolor: str = "white",
        color: str = "blue"
    ) -> Dict[str, Any]:
        """Generate audio waveform image."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-filter_complex",
            f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors={color}",
            "-frames:v", "1",
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_preview(
        self,
        input_path: str,
        output_path: str,
        duration: int = 10,
        width: int = 480,
        start_time: str = "0"
    ) -> Dict[str, Any]:
        """Generate video preview clip."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-ss", start_time,
            "-t", str(duration),
            "-vf", f"scale={width}:-1",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "28",
            "-c:a", "aac",
            "-b:a", "128k",
            "-threads", str(self.threads),
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except asyncio.TimeoutError:
            return {"success": False, "error": "Preview generation timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_gif(
        self,
        input_path: str,
        output_path: str,
        start_time: str = "0",
        duration: int = 5,
        width: int = 320
    ) -> Dict[str, Any]:
        """Create GIF from video."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-ss", start_time,
            "-t", str(duration),
            "-vf", f"fps=15,scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
            "-loop", "0",
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def take_screenshot(
        self,
        input_path: str,
        output_path: str,
        timestamp: str = "00:00:01"
    ) -> Dict[str, Any]:
        """Take screenshot at specific timestamp."""
        args = [
            "ffmpeg",
            "-i", input_path,
            "-ss", timestamp,
            "-vframes", "1",
            "-y",
            output_path
        ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def burn_subtitles(
        self,
        input_path: str,
        subtitle_path: str,
        output_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Burn subtitles into video."""
        if language:
            args = [
                "ffmpeg",
                "-i", input_path,
                "-i", subtitle_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-c:s", "srt",
                "-map", "0:v",
                "-map", "0:a",
                "-map", "1",
                "-metadata:s:s", f"language={language}",
                "-y",
                output_path
            ]
        else:
            args = [
                "ffmpeg",
                "-i", input_path,
                "-i", subtitle_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-c:s", "srt",
                "-y",
                output_path
            ]

        loop = asyncio.get_event_loop()
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)

            if proc.returncode == 0:
                return {"success": True, "output_path": output_path}
            return {"success": False, "error": stderr.decode()[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_version(self) -> str:
        """Get FFmpeg version."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.split("\n")[0]
        except Exception:
            return "unknown"


ffmpeg_service = FFmpegService()