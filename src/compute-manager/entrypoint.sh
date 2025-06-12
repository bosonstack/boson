#!/bin/bash
set -e

echo "Validating config..."
python /app/validate_worker_config.py

echo "Starting FastAPI server..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload