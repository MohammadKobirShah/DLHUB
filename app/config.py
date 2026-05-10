"""
DLHUB - Configuration Management
================================
Environment-based configuration with sensible defaults.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "DLHUB"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "High-performance open media downloading platform"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql://dlhub:dlhub123@postgres:5432/dlhub"

    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50

    DOWNLOAD_DIR: str = "/downloads"
    TEMP_DIR: str = "/tmp/dlhub"
    MAX_DOWNLOAD_SIZE: str = "5GB"
    MAX_DURATION: int = 7200
    MAX_CONCURRENT_DOWNLOADS: int = 50

    YTDLP_FORMAT: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    YTDLP_AUDIO_FORMAT: str = "bestaudio/best"
    YTDLP_EMBED_THUMBNAIL: bool = True
    YTDLP_ADD_METADATA: bool = True
    YTDLP_EMBED_CHAPTERS: bool = True
    YTDLP_WRITE_SUBTITLES: bool = True
    YTDLP_SUBTITLE_LANGS: str = "en,.*"
    YTDLP_EXTRACTOR_RETRIES: int = 3
    YTDLP_FRAGMENT_RETRIES: int = 5
    YTDLP_RETRIES: int = 5

    FFMPEG_THREADS: int = 4
    FFMPEG_TIMEOUT: int = 3600

    ENABLE_RATE_LIMIT: bool = False
    RATE_LIMIT_PER_MINUTE: int = 30
    ENABLE_SSRF_PROTECTION: bool = True

    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = "/downloads"

    COOKIES_FILE: str = "/cookies.txt"

    WORKER_COUNT: int = 4
    WORKER_TIMEOUT: int = 3600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()