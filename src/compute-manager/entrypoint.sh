#!/bin/bash
set -e

echo "Validating config..."
poetry run python /app/validate_worker_config.py

echo "Starting FastAPI server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload