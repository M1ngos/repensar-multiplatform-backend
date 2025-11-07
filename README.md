# Repensar Multiplatform Backend

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/downloads/release/python-311/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-green.svg)](https://fastapi.tiangolo.com/)
[![Alembic](https://img.shields.io/badge/Alembic-1.11.1-orange.svg)](https://alembic.sqlalchemy.org/en/latest/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

This is the backend for the Repensar Multiplatform project, built with FastAPI.

## ✨ Features

*   User Authentication (JWT based)
*   Project Management
*   Volunteer Management
*   Task Management
*   Resource Management

## 🚀 Getting Started

### Prerequisites

*   Python 3.11+
*   `uv` package installer

### 1. Clone the repository

```bash
git clone <repository-url>
cd repensar-multiplatform-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

This project uses `uv` for dependency management.

```bash
pip install uv
uv sync
```

### 4. Environment Configuration

Create a `.env` file from the example and fill in your environment variables.

```bash
cp .env.example .env
```

### 5. Database Setup with Alembic

This project uses Alembic exclusively for database migrations and schema management.

#### Configure Database Connection

Make sure your `.env` file has the `DATABASE_URL` set:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Alternatively, you can set it in `alembic.ini`:

```ini
# alembic.ini
sqlalchemy.url = postgresql://user:password@host:5432/dbname
```

#### Run Migrations

To create all tables and seed initial data:

```bash
alembic upgrade head
```

This will:
- Create all database tables with proper constraints and indexes
- Set up PostgreSQL functions and triggers
- Create database views for reporting
- Seed initial user types (admin, project_manager, staff_member, volunteer)

#### Check Migration Status

```bash
alembic current
```

#### Rollback a Migration

```bash
alembic downgrade -1
```

#### Create a New Migration

When you modify models, create a new migration:

```bash
alembic revision --autogenerate -m "description of changes"
```

Then review the generated migration file and apply it:

```bash
alembic upgrade head
```

## 🏃 Running the Application

To run the development server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## ✅ Running Tests

To run the test suite:

```bash
pytest
```

## 🐳 Docker Support

You can also run the application using Docker Compose.

```bash
docker-compose up -d
```
