# app/models/file.py
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class FileCategory(str, Enum):
    """File categories for organization."""
    profile_photo = "profile_photo"
    project_image = "project_image"
    task_attachment = "task_attachment"
    document = "document"
    timelog_receipt = "timelog_receipt"
    other = "other"


class StorageBackend(str, Enum):
    """Storage backend types."""
    local = "local"
    s3 = "s3"


class UploadedFile(SQLModel, table=True):
    """
    Tracks uploaded files with metadata.
    Supports both local and S3 storage.
    """
    __tablename__ = "uploaded_files"

    id: Optional[int] = Field(default=None, primary_key=True)

    # File information
    filename: str = Field(max_length=255, description="Original filename")
    file_path: str = Field(max_length=500, description="Storage path or S3 key")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(max_length=100, description="MIME type (e.g., image/jpeg)")
    category: FileCategory = Field(default=FileCategory.other)

    # Storage
    storage_backend: StorageBackend = Field(default=StorageBackend.local)
    bucket_name: Optional[str] = Field(default=None, max_length=100, description="S3 bucket name if using S3")

    # Image-specific (if applicable)
    width: Optional[int] = Field(default=None, description="Image width in pixels")
    height: Optional[int] = Field(default=None, description="Image height in pixels")
    thumbnail_path: Optional[str] = Field(default=None, max_length=500, description="Path to thumbnail")

    # Ownership and relations
    uploaded_by_id: int = Field(foreign_key="users.id", description="User who uploaded the file")
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id", index=True)
    task_id: Optional[int] = Field(default=None, foreign_key="tasks.id", index=True)
    volunteer_id: Optional[int] = Field(default=None, foreign_key="volunteers.id", index=True)

    # Metadata
    description: Optional[str] = Field(default=None, max_length=500)
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "profile_photo.jpg",
                "file_size": 102400,
                "mime_type": "image/jpeg",
                "category": "profile_photo",
                "uploaded_by_id": 1
            }
        }
