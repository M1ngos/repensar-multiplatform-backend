# app/routers/files.py
"""
File upload and management API.
Supports images, documents, and attachments for projects, tasks, and profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Form
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Optional, List
import logging
import magic

from app.core.deps import get_current_user, get_db
from app.core.storage import get_storage_service
from app.core.config import settings
from app.models.user import User
from app.models.file import UploadedFile, FileCategory, StorageBackend
from pydantic import BaseModel

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)


# Schemas
class FileResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    mime_type: str
    category: FileCategory
    url: str
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: str

    class Config:
        from_attributes = True


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    category: FileCategory = Form(FileCategory.other),
    project_id: Optional[int] = Form(None),
    task_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a file (image or document).

    **Supported file types:**
    - Images: JPEG, PNG, GIF, WEBP
    - Documents: PDF, DOC, DOCX

    **Size limit:** 10MB
    """
    try:
        # Read file content
        file_content = await file.read()

        # Check file size
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum {settings.MAX_FILE_SIZE / 1024 / 1024}MB"
            )

        # Detect MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(file_content)

        # Validate file type
        allowed_types = settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_DOCUMENT_TYPES
        if mime_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {mime_type}"
            )

        # Get storage service
        storage = get_storage_service()

        # Validate images
        is_image = mime_type.startswith("image/")
        if is_image and not storage.validate_image(file_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or corrupted image file"
            )

        # Save file
        file_path, file_size = await storage.save_file(
            file_content=file_content,
            filename=file.filename,
            category=category.value,
            user_id=current_user.id
        )

        # Get image dimensions if image
        width, height = None, None
        thumbnail_path = None

        if is_image:
            width, height = storage.get_image_dimensions(file_content)

            # Create thumbnail
            try:
                thumbnail_content = storage.create_thumbnail(file_content)
                thumbnail_filename = f"thumb_{file.filename}"
                thumbnail_path, _ = await storage.save_file(
                    file_content=thumbnail_content,
                    filename=thumbnail_filename,
                    category="thumbnails",
                    user_id=current_user.id
                )
            except Exception as e:
                logger.warning(f"Failed to create thumbnail: {e}")

        # Save to database
        uploaded_file = UploadedFile(
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            category=category,
            storage_backend=StorageBackend(settings.STORAGE_BACKEND),
            bucket_name=settings.S3_BUCKET if settings.STORAGE_BACKEND == "s3" else None,
            width=width,
            height=height,
            thumbnail_path=thumbnail_path,
            uploaded_by_id=current_user.id,
            project_id=project_id,
            task_id=task_id,
            description=description
        )

        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)

        logger.info(f"File uploaded: {uploaded_file.id} by user {current_user.id}")

        # Generate URLs
        file_url = await storage.get_file_url(file_path)
        thumbnail_url = await storage.get_file_url(thumbnail_path) if thumbnail_path else None

        return FileResponse(
            id=uploaded_file.id,
            filename=uploaded_file.filename,
            file_size=uploaded_file.file_size,
            mime_type=uploaded_file.mime_type,
            category=uploaded_file.category,
            url=file_url,
            thumbnail_url=thumbnail_url,
            width=uploaded_file.width,
            height=uploaded_file.height,
            created_at=uploaded_file.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed"
        )


@router.get("", response_model=List[FileResponse])
async def list_files(
    category: Optional[FileCategory] = None,
    project_id: Optional[int] = None,
    task_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of uploaded files with filters."""
    query = select(UploadedFile)

    # Apply filters
    if category:
        query = query.where(UploadedFile.category == category)
    if project_id:
        query = query.where(UploadedFile.project_id == project_id)
    if task_id:
        query = query.where(UploadedFile.task_id == task_id)

    # User can see files they uploaded or public files
    # TODO: Add permission checks for project/task access
    query = query.where(
        (UploadedFile.uploaded_by_id == current_user.id) |
        (UploadedFile.is_public == True)
    )

    query = query.offset(offset).limit(limit).order_by(UploadedFile.created_at.desc())

    files = db.exec(query).all()

    storage = get_storage_service()
    result = []

    for file in files:
        file_url = await storage.get_file_url(file.file_path)
        thumbnail_url = await storage.get_file_url(file.thumbnail_path) if file.thumbnail_path else None

        result.append(FileResponse(
            id=file.id,
            filename=file.filename,
            file_size=file.file_size,
            mime_type=file.mime_type,
            category=file.category,
            url=file_url,
            thumbnail_url=thumbnail_url,
            width=file.width,
            height=file.height,
            created_at=file.created_at.isoformat()
        ))

    return result


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get file by ID."""
    file = db.get(UploadedFile, file_id)

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    # TODO: Add permission checks for project/task access
    if file.uploaded_by_id != current_user.id and not file.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    storage = get_storage_service()
    file_url = await storage.get_file_url(file.file_path)
    thumbnail_url = await storage.get_file_url(file.thumbnail_path) if file.thumbnail_path else None

    return FileResponse(
        id=file.id,
        filename=file.filename,
        file_size=file.file_size,
        mime_type=file.mime_type,
        category=file.category,
        url=file_url,
        thumbnail_url=thumbnail_url,
        width=file.width,
        height=file.height,
        created_at=file.created_at.isoformat()
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete file."""
    file = db.get(UploadedFile, file_id)

    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check permissions
    if file.uploaded_by_id != current_user.id:
        # TODO: Allow project managers to delete project files
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete from storage
    storage = get_storage_service()
    await storage.delete_file(file.file_path)

    if file.thumbnail_path:
        await storage.delete_file(file.thumbnail_path)

    # Delete from database
    db.delete(file)
    db.commit()

    logger.info(f"File deleted: {file_id} by user {current_user.id}")

    return {"message": "File deleted successfully"}
