"""
DLHUB - Database Connection and Session Management
====================================================
PostgreSQL connection handling with SQLAlchemy.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

import logging
from contextlib import contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings
from app.constants import API_VERSION

logger = logging.getLogger(__name__)

DATABASE_DRIVER = "postgresql+asyncpg"
DATABASE_URL_ASYNC = settings.DATABASE_URL.replace(
    "postgresql://", DATABASE_DRIVER + "://"
).replace("postgres://", DATABASE_DRIVER + "://")

engine = create_async_engine(
    DATABASE_URL_ASYNC,
    echo=settings.DEBUG,
    poolclass=NullPool,
    pool_pre_ping=True,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def init_db():
    """Initialize database tables."""
    logger.info("Initializing database...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.info("Tables may already exist, continuing...")
        pass


async def close_db():
    """Close database connections."""
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_db_sync():
    """Get synchronous database session for background tasks."""
    import logging
    import time
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    logger = logging.getLogger(__name__)
    start_time = time.time()
    
    sync_db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql://")
    logger.debug(f"Creating new sync engine for database connection: {sync_db_url.split('@')[1] if '@' in sync_db_url else 'configured'}")
    
    sync_engine = create_engine(sync_db_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
    sync_session = sessionmaker(bind=sync_engine)

    session = sync_session()
    try:
        logger.debug(f"Database session created in {time.time() - start_time:.3f}s")
        yield session
        session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug(f"Database session closed after {time.time() - start_time:.3f}s")
        # Don't dispose the engine here - let it be managed by the application lifecycle


async def get_db_context() -> AsyncSession:
    """Get database session context manager."""
    return async_session_maker()