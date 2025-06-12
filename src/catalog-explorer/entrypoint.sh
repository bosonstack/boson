#!/bin/bash
set -e

echo "Launching Experiment Tracker..."

exec python -m uvicorn app:app --host 0.0.0.0 --port 8002 --reload