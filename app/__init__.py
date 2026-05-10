"""
DLHUB - High-Performance Media Downloading Platform
=====================================================
A production-grade open media backend powered by yt-dlp + FFmpeg.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

__version__ = "1.0.0"
__app_name__ = "DLHUB"
__description__ = "High-performance open media downloading platform"
__author__ = "Md Kobir Shah"

from app.main import app

__all__ = ["app"]