#!/bin/bash
set -e

echo "📦 Downloading FlintML..."
curl -L -o flintml.tar.gz https://github.com/flintml/flint/releases/latest/download/flintml.tar.gz

echo "📂 Extracting package..."
tar xzf flintml.tar.gz

cd flintml-* || { echo "❌ Failed to find extracted directory"; exit 1; }

echo "🐳 Starting Docker Compose stack..."
docker compose -f docker-compose.*.yml up