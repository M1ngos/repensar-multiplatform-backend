from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.database.engine import create_db_and_tables
from app.routers import auth, volunteers, projects, tasks, resources, reports, auth_enhanced
from app.models import user, volunteer, project, task, resource, analytics
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database and tables on startup
    logger.info("Creating database tables...")
    create_db_and_tables()

    # Initialize Redis if available
    try:
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            logger.info(f"Initializing Redis connection: {settings.REDIS_URL}")
            from redis import Redis
            from app.core.token_manager import initialize_redis_blacklist
            from app.core.rate_limiter import initialize_redis_rate_limiter

            redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,
                socket_connect_timeout=5
            )

            # Test connection
            redis_client.ping()

            # Initialize Redis-backed services
            initialize_redis_blacklist(redis_client)
            initialize_redis_rate_limiter(redis_client)
            logger.info("✓ Redis initialized successfully")
        else:
            logger.info("Redis not configured, using in-memory storage (development mode)")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis: {e}")
        logger.warning("Falling back to in-memory storage")

    logger.info("Application startup complete")

    yield

    logger.info("Application shutdown")

app = FastAPI(
    title="Repensar Multiplatform Backend",
    description="Backend API for Repensar multiplatform application with production-grade JWT authentication",
    version="2.0.0",
    lifespan=lifespan
)

# Include routers - v2 (primary) registered first
app.include_router(auth_enhanced.router)  # Primary: /auth/*
app.include_router(auth.router)           # Legacy: /auth/v1/*
app.include_router(volunteers.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(resources.router)
app.include_router(reports.router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Repensar Backend API",
        "version": "2.0.0",
        "authentication": {
            "current": "/auth/* (v2 - production-grade JWT with token rotation)",
            "legacy": "/auth/v1/* (v1 - basic JWT, deprecated)"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
