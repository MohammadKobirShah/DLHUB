"""
DLHUB - Routers Package
=======================
API route handlers.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from app.routers import download, system, files, queue, media, youtube, admin, websocket

__all__ = ["download", "system", "files", "queue", "media", "youtube", "admin", "websocket"]