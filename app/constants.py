"""
DLHUB - Constants and Enumerations
==================================
Application-wide constants, enums, and default values.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from enum import Enum


class DownloadStatus(str, Enum):
    """Download job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadType(str, Enum):
    """Type of download."""
    VIDEO = "video"
    AUDIO = "audio"
    PLAYLIST = "playlist"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    """Supported output formats."""
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
    WAV = "wav"
    AAC = "aac"
    OGG = "ogg"


DEFAULT_VIDEO_FORMAT = "mp4"
DEFAULT_AUDIO_FORMAT = "mp3"

VIDEO_QUALITY_PRESETS = {
    "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "2160p": "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]/best",
    "1440p": "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440][ext=mp4]/best",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
    "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
    "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
    "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
    "240p": "bestvideo[height<=240][ext=mp4]+bestaudio[ext=m4a]/best[height<=240][ext=mp4]/best",
    "144p": "bestvideo[height<=144][ext=mp4]+bestaudio[ext=m4a]/best[height<=144][ext=mp4]/best",
}

AUDIO_FORMAT_PRESETS = {
    "mp3": "bestaudio[ext=m4a]/bestaudio",
    "m4a": "bestaudio",
    "flac": "bestaudio[ext=flac]/bestaudio",
    "wav": "bestaudio",
    "aac": "bestaudio[ext=m4a]/bestaudio",
    "ogg": "bestaudio[ext=ogg]/bestaudio",
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024 * 1024
MAX_DURATION_SECONDS = 7200

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

BLOCKED_IP_RANGES = [
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "127.0.0.0/8",
    "169.254.0.0/16",
    "0.0.0.0/8",
    "100.64.0.0/10",
    "192.0.0.0/24",
    "192.0.2.0/24",
    "198.51.100.0/24",
    "203.0.113.0/24",
    "fc00::/7",
    "fe80::/10",
]

YT_DLP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

DOWNLOAD_CHUNK_SIZE = 1024 * 1024

PROGRESS_UPDATE_INTERVAL = 1.0

YT_DLP_EXTRACTORS = [
    "youtube",
    "youtube:playlist",
    "youtube:search",
    "youtube:channel",
    "youtube:live",
    "vimeo",
    "dailymotion",
    "soundcloud",
    "twitch",
    "bilibili",
]