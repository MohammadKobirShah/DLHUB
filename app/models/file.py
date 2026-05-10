"""
DLHUB - File Model
===================
SQLAlchemy model for downloaded files.

Developer: Md Kobir Shah
GitHub: @MohammadKobirShah
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    Text,
    Boolean,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.database import Base


class File(Base):
    """Downloaded file database model."""

    __tablename__ = "files"

    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True)
    job_id = Column(PGUUID(as_uuid=True), nullable=True, index=True)

    file_name = Column(String(500), nullable=False, index=True)
    file_path = Column(Text, nullable=False)

    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    extension = Column(String(20), nullable=True)

    is_video = Column(Boolean, nullable=True, default=False)
    is_audio = Column(Boolean, nullable=True, default=False)
    is_image = Column(Boolean, nullable=True, default=False)
    is_subtitle = Column(Boolean, nullable=True, default=False)

    thumbnail_path = Column(Text, nullable=True)
    info_json_path = Column(Text, nullable=True)
    subtitle_paths = Column(JSON, nullable=True)

    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    uploader = Column(String(500), nullable=True)
    upload_date = Column(DateTime, nullable=True)

    duration = Column(BigInteger, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)

    codec = Column(String(50), nullable=True)
    audio_codec = Column(String(50), nullable=True)

    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)

    downloads = Column(BigInteger, nullable=True, default=0)
    last_downloaded_at = Column(DateTime, nullable=True)

    is_deleted = Column(Boolean, nullable=True, default=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<File {self.file_name}>"

    def to_dict(self):
        """Convert file to dictionary."""
        return {
            "id": str(self.id),
            "job_id": str(self.job_id) if self.job_id else None,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "is_video": self.is_video,
            "is_audio": self.is_audio,
            "title": self.title,
            "uploader": self.uploader,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "downloads": self.downloads,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }