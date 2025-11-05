# app/core/storage.py
"""
File storage service supporting local filesystem and AWS S3.
"""
import os
import uuid
import hashlib
import logging
import aiofiles
from pathlib import Path
from typing import Optional, Tuple, BinaryIO
from datetime import datetime

from PIL import Image
import io

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for storing and retrieving files.
    Supports both local filesystem and S3 storage.
    """

    def __init__(
        self,
        storage_backend: str = "local",
        upload_dir: str = "./uploads",
        s3_bucket: Optional[str] = None,
        s3_region: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
    ):
        """
        Initialize storage service.

        Args:
            storage_backend: "local" or "s3"
            upload_dir: Directory for local storage
            s3_bucket: S3 bucket name (if using S3)
            s3_region: S3 region (if using S3)
            max_file_size: Maximum file size in bytes
        """
        self.storage_backend = storage_backend
        self.upload_dir = Path(upload_dir)
        self.s3_bucket = s3_bucket
        self.s3_region = s3_region
        self.max_file_size = max_file_size

        # Create upload directory if using local storage
        if storage_backend == "local":
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            (self.upload_dir / "thumbnails").mkdir(exist_ok=True)

        # Initialize S3 client if using S3
        self.s3_client = None
        if storage_backend == "s3":
            try:
                import boto3
                self.s3_client = boto3.client("s3", region_name=s3_region)
                logger.info(f"S3 storage initialized: bucket={s3_bucket}, region={s3_region}")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                raise

    def generate_filename(self, original_filename: str, user_id: int) -> str:
        """
        Generate a unique filename.

        Args:
            original_filename: Original uploaded filename
            user_id: User ID for namespacing

        Returns:
            Unique filename with original extension
        """
        # Get file extension
        ext = Path(original_filename).suffix.lower()

        # Generate unique ID
        unique_id = str(uuid.uuid4())

        # Create timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Format: {user_id}_{timestamp}_{uuid}.{ext}
        return f"{user_id}_{timestamp}_{unique_id}{ext}"

    def get_file_path(self, filename: str, category: str = "general") -> str:
        """
        Get storage path for a file.

        Args:
            filename: Generated filename
            category: File category for organization

        Returns:
            Full file path or S3 key
        """
        if self.storage_backend == "local":
            return str(self.upload_dir / category / filename)
        else:
            # S3 key
            return f"{category}/{filename}"

    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        category: str = "general",
        user_id: int = 0
    ) -> Tuple[str, int]:
        """
        Save file to storage.

        Args:
            file_content: File content as bytes
            filename: Original filename
            category: File category
            user_id: User ID

        Returns:
            Tuple of (storage_path, file_size)
        """
        # Check file size
        file_size = len(file_content)
        if file_size > self.max_file_size:
            raise ValueError(f"File size {file_size} exceeds maximum {self.max_file_size}")

        # Generate unique filename
        unique_filename = self.generate_filename(filename, user_id)
        storage_path = self.get_file_path(unique_filename, category)

        if self.storage_backend == "local":
            # Save to local filesystem
            file_path = Path(storage_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(file_content)

            logger.info(f"Saved file locally: {storage_path}")

        else:
            # Save to S3
            try:
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=storage_path,
                    Body=file_content,
                )
                logger.info(f"Saved file to S3: {storage_path}")
            except Exception as e:
                logger.error(f"Failed to save file to S3: {e}")
                raise

        return storage_path, file_size

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Path to file (local or S3 key)

        Returns:
            True if deleted successfully
        """
        try:
            if self.storage_backend == "local":
                path = Path(file_path)
                if path.exists():
                    path.unlink()
                    logger.info(f"Deleted file: {file_path}")
                    return True
            else:
                # Delete from S3
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket,
                    Key=file_path
                )
                logger.info(f"Deleted file from S3: {file_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def get_file_url(self, file_path: str, expiration: int = 3600) -> str:
        """
        Get URL for accessing file.

        Args:
            file_path: Path to file
            expiration: URL expiration in seconds (S3 only)

        Returns:
            File URL
        """
        if self.storage_backend == "local":
            # For local files, return relative path (served by FastAPI static files)
            return f"/files/{file_path}"
        else:
            # Generate presigned S3 URL
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.s3_bucket, "Key": file_path},
                    ExpiresIn=expiration
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate presigned URL: {e}")
                raise

    def create_thumbnail(
        self,
        image_content: bytes,
        max_size: Tuple[int, int] = (300, 300),
        quality: int = 85
    ) -> bytes:
        """
        Create thumbnail from image.

        Args:
            image_content: Original image content
            max_size: Maximum thumbnail dimensions (width, height)
            quality: JPEG quality (1-100)

        Returns:
            Thumbnail image as bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_content))

            # Convert RGBA to RGB if necessary
            if image.mode in ("RGBA", "LA", "P"):
                # Create a white background
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background

            # Create thumbnail
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = io.BytesIO()
            image.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

            return output.read()

        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            raise

    def get_image_dimensions(self, image_content: bytes) -> Tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image_content: Image content as bytes

        Returns:
            Tuple of (width, height)
        """
        try:
            image = Image.open(io.BytesIO(image_content))
            return image.size
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
            return (0, 0)

    def validate_image(self, image_content: bytes, max_dimensions: Tuple[int, int] = (4000, 4000)) -> bool:
        """
        Validate image file.

        Args:
            image_content: Image content as bytes
            max_dimensions: Maximum allowed dimensions

        Returns:
            True if valid
        """
        try:
            image = Image.open(io.BytesIO(image_content))

            # Check dimensions
            if image.width > max_dimensions[0] or image.height > max_dimensions[1]:
                logger.warning(f"Image dimensions {image.size} exceed maximum {max_dimensions}")
                return False

            # Check format
            if image.format not in ["JPEG", "PNG", "GIF", "WEBP"]:
                logger.warning(f"Unsupported image format: {image.format}")
                return False

            return True

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False


# Global storage instance
_storage_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get the global storage service instance."""
    global _storage_instance
    if _storage_instance is None:
        from app.core.config import settings

        _storage_instance = StorageService(
            storage_backend=getattr(settings, "STORAGE_BACKEND", "local"),
            upload_dir=getattr(settings, "UPLOAD_DIR", "./uploads"),
            s3_bucket=getattr(settings, "S3_BUCKET", None),
            s3_region=getattr(settings, "S3_REGION", None),
            max_file_size=getattr(settings, "MAX_FILE_SIZE", 10 * 1024 * 1024),
        )
    return _storage_instance
