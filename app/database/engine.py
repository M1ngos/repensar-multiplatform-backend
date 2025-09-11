from sqlmodel import create_engine, SQLModel, Session
from typing import Generator
import os

from app.core.config import settings

# Use PostgreSQL database URL
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    echo=True if os.getenv("DEBUG") else False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session