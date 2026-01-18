#!/usr/bin/env sh

set -e

# Ensure the /app directory (where the FastAPI project lives) is on PYTHONPATH
export PYTHONPATH=/app

# Run database migrations
alembic upgrade head

# Start the application
exec "$@"