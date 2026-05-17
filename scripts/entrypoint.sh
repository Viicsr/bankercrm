#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied"

if [ "$APP_ENV" = "production" ]; then
    echo "Starting FastAPI server (production mode)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
else
    echo "Starting FastAPI server (development mode)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi