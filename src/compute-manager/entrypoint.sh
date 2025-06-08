#!/bin/bash
set -e

echo "Validating config..."


echo "Starting FastAPI server..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload