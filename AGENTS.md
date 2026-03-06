# AGENTS.md — Repensar Multiplatform Backend

## Project Overview

Python **FastAPI** backend with **SQLModel** (SQLAlchemy + Pydantic ORM), **PostgreSQL**, and optional **Redis**. Uses `uv` as the package manager.

---

## Environment Setup

```bash
uv sync                        # Install all dependencies
cp .env.example .env           # Configure environment variables
docker-compose up -d           # Start PostgreSQL + Redis
alembic upgrade head           # Apply DB migrations
uvicorn app.main:app --reload  # Start dev server (http://localhost:8000)
```

---

## Build / Run Commands

```bash
uvicorn app.main:app --reload              # Dev server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production-like
docker-compose up --build                 # Full stack via Docker
```

---

## Database Migrations

```bash
alembic upgrade head                              # Apply all migrations
alembic revision --autogenerate -m "description" # Generate new migration
alembic downgrade -1                              # Roll back one step
alembic history                                   # Show migration history
```

Always create a migration after changing any SQLModel model with `table=True`.

---

## Testing

Framework: **pytest** with **pytest-asyncio** and **httpx**. Tests run against an in-memory **SQLite** database — no external services required.

```bash
pytest                                                    # Run all tests
pytest -v                                                 # Verbose output
pytest -s                                                 # Show print/log output
pytest tests/test_auth_routes.py                          # Single file
pytest tests/test_auth_routes.py::TestAuthLogin           # Single class
pytest tests/test_auth_routes.py::TestAuthLogin::test_login_success  # Single test
pytest -k "test_login_success"                            # By name pattern
pytest -m unit                                            # By marker
pytest -m "not slow"                                      # Exclude slow tests
pytest --tb=short                                         # Short tracebacks (default)
```

**Test markers**: `slow`, `integration`, `unit` (declare with `@pytest.mark.<marker>`).

**Key fixtures** (`tests/conftest.py`):
- `session` — SQLite in-memory `Session`
- `client` — FastAPI `TestClient` with DB overridden to SQLite
- `user_types` — seeds `UserType` records (admin, volunteer, project_manager, staff_member)
- `test_user` — creates a verified user in test DB
- `auth_headers` — returns `{"Authorization": "Bearer <token>"}` for a logged-in user

**Test environment**: Set `DISABLE_RATE_LIMITING=True` in `.env` (or `os.environ`) to bypass rate limits during testing.

---

## Code Style

### Python Version
Requires **Python 3.11+**. Use modern type hints (`list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]` where appropriate, though existing code uses `typing` imports for consistency).

### Import Order
Follow this strict grouping with blank lines between sections:
```python
# 1. Standard library
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import logging

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, SQLModel, Field

# 3. Internal (app.*)
from app.core.deps import get_current_user, get_current_active_user
from app.models.volunteer import Volunteer
from app.schemas.volunteer import VolunteerCreate, VolunteerUpdate
from app.crud.volunteer import volunteer_crud
```

### Naming Conventions
| Target | Convention | Example |
|---|---|---|
| Files/modules | `snake_case` | `auth_enhanced.py` |
| Classes | `PascalCase` | `VolunteerCRUD`, `GamificationService` |
| Functions/methods | `snake_case` | `get_current_user`, `create_access_token` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_RATE_LIMITS`, `MAX_LOGIN_ATTEMPTS` |
| Enum values | `"snake_case"` strings | `TaskStatus.not_started = "not_started"` |
| Private helpers | `_snake_case` | `_can_manage_project`, `_is_rate_limiting_disabled` |
| CRUD singletons | module-level lowercase | `volunteer_crud = VolunteerCRUD()` |

### Schema Pattern
Always follow this four-class schema hierarchy for each domain:
```python
class FooBase(BaseModel):          # shared fields with validators
    ...

class FooCreate(FooBase):          # creation fields (user-provided only)
    ...

class FooUpdate(BaseModel):        # all fields Optional for PATCH semantics
    field: Optional[type] = None

class Foo(FooBase):                # full DB response schema
    id: int
    created_at: datetime
    class Config:
        from_attributes = True     # ORM mode
```

### CRUD Class Pattern
```python
class FooCRUD:
    def get(self, db: Session, id: int) -> Optional[Foo]:
        return db.get(Foo, id)                              # simple PK lookup

    def get_multi(self, db: Session, ...) -> list[Foo]:
        return db.exec(select(Foo).where(...)).all()        # filtered query

    def create(self, db: Session, data: FooCreate) -> Foo:
        obj = Foo(**data.model_dump())
        db.add(obj); db.commit(); db.refresh(obj)
        return obj

    def update(self, db: Session, id: int, data: FooUpdate) -> Optional[Foo]:
        obj = self.get(db, id)
        if not obj:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():  # only set fields
            setattr(obj, k, v)
        db.add(obj); db.commit(); db.refresh(obj)
        return obj

foo_crud = FooCRUD()   # module-level singleton
```

**Always use `model_dump(exclude_unset=True)`** in update operations to implement proper PATCH semantics.

### Database Queries
```python
# Preferred patterns (SQLModel)
db.get(Model, id)                                     # PK lookup
db.exec(select(Model).where(Model.field == val)).first()  # single result
db.exec(select(Model).where(...)).all()               # list result

# Never use legacy SQLAlchemy style
db.query(Model).filter(...)   # WRONG — do not use
```

For joins requiring related objects, use `selectinload` to avoid N+1 queries:
```python
statement = select(User).options(selectinload(User.user_type)).where(...)
```

### Error Handling in Routers
```python
@router.get("/{id}")
async def get_foo(id: int, db: Session = Depends(get_db)):
    try:
        result = foo_crud.get(db, id)
        if not result:
            raise HTTPException(status_code=404, detail="Foo not found")
        return result
    except HTTPException:
        raise                          # always re-raise FastAPI exceptions unchanged
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve foo: {str(e)}"
        )
```

### Error Handling in Services
Services log errors and do not propagate exceptions to callers:
```python
try:
    await callback(payload)
except Exception as e:
    logger.error(f"Error in event subscriber for {event_type}: {e}")
```

### Logging
Use module-level loggers, never `print()`:
```python
logger = logging.getLogger(__name__)
logger.info("Action completed: %s", detail)
logger.error("Failed to do X: %s", e)
```

---

## Architecture

```
app/
├── main.py          # FastAPI app, lifespan, CORS, router registration
├── core/            # Cross-cutting: auth, deps, config, rate limiter, token manager
├── models/          # SQLModel ORM models (table=True)
├── schemas/         # Pydantic request/response schemas
├── crud/            # Data access layer (CRUD classes)
├── routers/         # Route handlers (thin — delegate to crud/services)
├── services/        # Business logic, event bus, notifications
└── database/        # Engine, session factory, get_db()
```

**Layering rule**: Routers call CRUD and Services. Services may call CRUD. CRUD only calls the DB. No cross-layer circular imports.

---

## Auth & Permissions

- JWT (HS256) via `python-jose`. Access tokens: 30 min. Refresh tokens: 30 days with family rotation.
- Dependency chain: `get_current_user` → `get_current_active_user` (use appropriate one per endpoint).
- Role checks use string comparison: `current_user.user_type.name in ("admin", "project_manager")`.
- User roles: `"admin"`, `"volunteer"`, `"project_manager"`, `"staff_member"`.
- Rate limiting is enforced per-IP. Bypass with `DISABLE_RATE_LIMITING=True` (dev/test only).

---

## Key Conventions

- **Soft deletes**: Set status to `"inactive"`, never `DELETE` from DB for volunteers.
- **Pagination**: Use `PaginatedResponse[T]` (`app/schemas/common.py`) for all list endpoints.
- **Enum query params**: Validate with `Query(None, regex="^(value1|value2)$")`.
- **Generic responses**: `SuccessResponse` and `ErrorResponse` from `app/schemas/common.py`.
- **Startup wiring**: Redis, EventBus, SSEManager, GamificationService, and BackgroundTaskManager are all initialized in `main.py` lifespan — add new startup logic there.
- **Two auth routers**: `auth_enhanced.py` (`/auth/*`) is primary (production). `auth.py` (`/auth/v1/*`) is legacy — do not add new endpoints there.
