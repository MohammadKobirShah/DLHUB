"""
DLHUB - Main FastAPI Application Entry Point
=============================================
Production-grade media downloading API service.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.routers import download, system, files, queue, media, youtube, admin, websocket
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    import signal
    import asyncio
    
    # Setup signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        shutdown_event.set()
    
    # Register signal handlers
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    except (AttributeError, ValueError):
        # Not available in all environments (like Windows)
        pass
    
    try:
        logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
        logger.info(f"Download directory: {settings.DOWNLOAD_DIR}")
        logger.info(f"Max concurrent downloads: {settings.MAX_CONCURRENT_DOWNLOADS}")
        logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")

        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    try:
        logger.info("Shutting down DLHUB...")
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "Md Kobir Shah",
        "url": "https://github.com/MohammadKobirShah"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(download.router, prefix="/api/v1", tags=["Download"])
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(queue.router, prefix="/api/v1", tags=["Queue"])
app.include_router(media.router, prefix="/api/v1", tags=["Media"])
app.include_router(youtube.router, prefix="/api/v1", tags=["YouTube"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(websocket.router, tags=["WebSocket"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs": "/api/v1/docs",
        "developer": "Md Kobir Shah",
        "github": "@MohammadKobirShah"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )