#!/bin/bash
set -e

# Check if /repo is empty
if [ -z "$(ls -A /repo)" ]; then
  echo "🔨 /repo is empty — initializing Aim repo…"
  aim init --repo /repo
else
  echo "✔️  /repo is not empty — skipping init."
fi

echo "🚀 Launching Aim server…"
exec aim server --repo /repo --host 0.0.0.0 --port 53800
