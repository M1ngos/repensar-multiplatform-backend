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

### 5. Database Migrations

Before running migrations, you need to set your database URL in `alembic.ini`.

Open `alembic.ini` and set the `sqlalchemy.url` variable:

```ini
# alembic.ini

[alembic]
...
sqlalchemy.url = postgresql://user:password@host/dbname
...
```

Once configured, run the migrations:

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
