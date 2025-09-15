from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database.engine import create_db_and_tables
from app.routers import auth, volunteers
from app.models import user, volunteer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database and tables on startup
    create_db_and_tables()
    yield

app = FastAPI(
    title="Repensar Multiplatform Backend",
    description="Backend API for Repensar multiplatform application",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(auth.router)
app.include_router(volunteers.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Repensar Backend API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
