from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # JWT Configuration
    SECRET_KEY: str = "St2vToKITZj7HxUvzfiegjf8LMfaCrwOuIIetLNIe8Y="  # IMPORTANT: Change in production!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: Optional[str] = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "repensar"
    DB_PASSWORD: str = "repensar_password"
    DB_NAME: str = "repensar_db"

    # Redis (optional - for production)
    REDIS_URL: Optional[str] = None  # e.g., "redis://localhost:6379/0"
    
    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Email
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: str = "Repensar"

    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    # Newsletter Configuration
    NEWSLETTER_FROM_EMAIL: Optional[str] = None  # Falls back to EMAIL_FROM
    NEWSLETTER_FROM_NAME: str = "Repensar Newsletter"
    ADMIN_NOTIFICATION_EMAIL: Optional[str] = None  # Email for contact form notifications
    CAMPAIGN_BATCH_SIZE: int = 50  # Emails to send per batch
    CAMPAIGN_BATCH_DELAY_SECONDS: float = 1.0  # Delay between emails (rate limiting)
    SUBSCRIPTION_CONFIRM_HOURS: int = 24  # Hours until confirmation link expires

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None  # e.g., "http://localhost:8000/auth/google/callback"

    # Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    DISABLE_RATE_LIMITING: bool = False  # Set to True for development/testing

    # File Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB in bytes
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    ALLOWED_DOCUMENT_TYPES: list[str] = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    # AWS S3 (if using S3 storage)
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Allow extra fields in .env file

settings = Settings()
