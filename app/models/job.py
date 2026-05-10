"""
DLHUB - Job Model
==================
SQLAlchemy model for download jobs.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    Text,
    Boolean,
    Float,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.constants import DownloadStatus, DownloadType


class Job(Base):
    """Download job database model."""

    __tablename__ = "jobs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    url = Column(Text, nullable=False, index=True)
    job_type = Column(SQLEnum(DownloadType), nullable=False, default=DownloadType.VIDEO)

    status = Column(
        SQLEnum(DownloadStatus),
        nullable=False,
        default=DownloadStatus.PENDING,
        index=True
    )

    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    uploader = Column(String(500), nullable=True)
    uploader_url = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)
    view_count = Column(BigInteger, nullable=True)
    like_count = Column(BigInteger, nullable=True)

    format = Column(String(50), nullable=True)
    quality = Column(String(50), nullable=True)
    output_format = Column(String(20), nullable=True, default="mp4")

    file_path = Column(Text, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    file_name = Column(String(500), nullable=True)
    mime_type = Column(String(100), nullable=True)

    extractor = Column(String(100), nullable=True)
    extractor_version = Column(String(50), nullable=True)

    progress = Column(Float, nullable=True, default=0.0)
    speed = Column(String(50), nullable=True)
    eta = Column(Integer, nullable=True)

    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)

    retries = Column(Integer, nullable=True, default=0)
    max_retries = Column(Integer, nullable=True, default=3)

    priority = Column(Integer, nullable=True, default=1)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Job {self.id} - {self.status.value}: {self.url[:50]}>"

    @property
    def is_active(self) -> bool:
        """Check if job is currently active."""
        return self.status in [
            DownloadStatus.PENDING,
            DownloadStatus.PROCESSING
        ]

    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == DownloadStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == DownloadStatus.FAILED

    def to_dict(self):
        """Convert job to dictionary."""
        return {
            "id": str(self.id),
            "url": self.url,
            "job_type": self.job_type.value if self.job_type else None,
            "status": self.status.value if self.status else None,
            "title": self.title,
            "description": self.description,
            "thumbnail_url": self.thumbnail_url,
            "uploader": self.uploader,
            "uploader_url": self.uploader_url,
            "duration": self.duration,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "format": self.format,
            "quality": self.quality,
            "output_format": self.output_format,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "file_name": self.file_name,
            "mime_type": self.mime_type,
            "extractor": self.extractor,
            "progress": self.progress,
            "speed": self.speed,
            "eta": self.eta,
            "error_message": self.error_message,
            "retries": self.retries,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }