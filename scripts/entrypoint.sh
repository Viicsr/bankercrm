#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations applied"

PORT=${PORT:-8000}

if [ "$APP_ENV" = "production" ]; then
    echo "Starting server (production) on port $PORT..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 2
else
    echo "Starting server (development) on port $PORT..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --reload
fi