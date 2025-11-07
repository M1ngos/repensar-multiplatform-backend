from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Database migrations are managed exclusively via Alembic
# from app.database.engine import create_db_and_tables
from app.routers import auth, volunteers, projects, tasks, resources, reports, auth_enhanced, sync, analytics, users, notifications, files, search
from app.models import user, volunteer, project, task, resource
from app.models import analytics as analytics_models
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTE: Database migrations are managed by Alembic exclusively.
    # Run: alembic upgrade head
    logger.info("Starting application...")

    # Initialize Redis and real-time services
    redis_async_client = None
    try:
        if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
            logger.info(f"Initializing Redis connection: {settings.REDIS_URL}")
            from redis import Redis
            import redis.asyncio as redis_async
            from app.core.token_manager import initialize_redis_blacklist
            from app.core.rate_limiter import initialize_redis_rate_limiter

            # Sync Redis client for token blacklist and rate limiter
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
            logger.info("✓ Redis (sync) initialized successfully")

            # Async Redis client for EventBus and real-time features
            redis_async_client = redis_async.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            await redis_async_client.ping()
            logger.info("✓ Redis (async) initialized successfully")
        else:
            logger.info("Redis not configured, using in-memory storage (development mode)")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis: {e}")
        logger.warning("Falling back to in-memory storage")

    # Initialize EventBus
    from app.services.event_bus import EventBus
    import app.services.event_bus as event_bus_module
    event_bus_module.event_bus = EventBus(redis_async_client)
    await event_bus_module.event_bus.initialize()
    await event_bus_module.event_bus.start_listener()
    logger.info("✓ EventBus initialized")

    # Initialize SSEManager
    from app.core.sse_manager import SSEManager
    import app.core.sse_manager as sse_manager_module
    sse_manager_module.sse_manager = SSEManager()
    await sse_manager_module.sse_manager.start_heartbeat()
    logger.info("✓ SSEManager initialized")

    # Subscribe to notification events for SSE broadcasting
    from app.services.event_bus import EventType
    event_bus = event_bus_module.event_bus

    async def broadcast_notification_to_sse(event_payload):
        """Broadcast notification events to SSE clients."""
        try:
            sse_manager = sse_manager_module.sse_manager
            user_id = event_payload.get("user_id")
            if user_id:
                await sse_manager.broadcast_to_user(
                    user_id,
                    "notification",
                    event_payload.get("data", {})
                )
        except Exception as e:
            logger.error(f"Error broadcasting notification to SSE: {e}")

    event_bus.subscribe(EventType.NOTIFICATION_CREATED, broadcast_notification_to_sse)
    logger.info("✓ SSE notification broadcasting enabled")

    # Initialize and start background tasks
    from app.core.background_tasks import BackgroundTaskManager
    import app.core.background_tasks as background_tasks_module
    background_tasks_module.background_task_manager = BackgroundTaskManager()
    await background_tasks_module.background_task_manager.start()
    logger.info("✓ Background tasks started")

    logger.info("Application startup complete")

    yield

    # Cleanup on shutdown
    logger.info("Application shutdown initiated...")

    # Stop background tasks
    if background_tasks_module.background_task_manager:
        await background_tasks_module.background_task_manager.stop()
        logger.info("✓ Background tasks stopped")

    # Stop EventBus listener
    if event_bus_module.event_bus:
        await event_bus_module.event_bus.stop_listener()
        logger.info("✓ EventBus stopped")

    # Stop SSE heartbeat
    if sse_manager_module.sse_manager:
        await sse_manager_module.sse_manager.stop_heartbeat()
        logger.info("✓ SSEManager stopped")

    # Close async Redis connection
    if redis_async_client:
        await redis_async_client.close()
        logger.info("✓ Redis (async) connection closed")

    logger.info("Application shutdown complete")

app = FastAPI(
    title="Repensar Multiplatform Backend",
    description="Backend API for Repensar multiplatform application with production-grade JWT authentication",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,  # Frontend URL from settings
        "http://localhost:3000",  # React default
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://192.168.1.81:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include routers - v2 (primary) registered first
app.include_router(auth_enhanced.router)  # Primary: /auth/*
app.include_router(auth.router)           # Legacy: /auth/v1/*
app.include_router(sync.router)           # Sync: /sync/* (offline-first)
app.include_router(users.router)          # Users: /users/* (user management)
app.include_router(notifications.router)  # Notifications: /notifications/* (real-time SSE)
app.include_router(files.router)          # Files: /files/* (file upload & management)
app.include_router(search.router)         # Search: /search/* (full-text search)
app.include_router(volunteers.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(resources.router)
app.include_router(reports.router)
app.include_router(analytics.router)      # Analytics: /analytics/* (time-series & dashboards)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Repensar Backend API",
        "version": "2.0.0",
        "authentication": {
            "current": "/auth/* (v2 - production-grade JWT with token rotation)",
            "legacy": "/auth/v1/* (v1 - basic JWT, deprecated)"
        },
        "modules": {
            "users": "/users/* (user management and search)",
            "notifications": "/notifications/* (real-time notifications via SSE)",
            "projects": "/projects/* (project management with relations)",
            "tasks": "/tasks/* (task tracking and assignments)",
            "volunteers": "/volunteers/* (volunteer profiles and management)",
            "resources": "/resources/* (resource allocation)",
            "analytics": "/analytics/* (time-series metrics and dashboards)",
            "reports": "/reports/* (reports and data exports)",
            "sync": "/sync/* (offline-first sync for mobile/desktop)"
        },
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
