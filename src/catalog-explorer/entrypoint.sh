#!/bin/bash
set -e

echo "Launching Experiment Tracker..."

exec poetry run uvicorn app:app --host 0.0.0.0 --port 8002 --reload
