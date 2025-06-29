#!/bin/bash
set -e

# Configure JucieFS
export AWS_ACCESS_KEY_ID="${STORAGE_USER}"
export AWS_SECRET_ACCESS_KEY="${STORAGE_PASSWORD}"
export AWS_REGION=us-east-1
export AWS_S3_FORCE_PATH_STYLE=1

mkdir -p "$(dirname "$META_PATH")"

META_URL="sqlite3://$META_PATH"

juicefs format \
  --storage s3 \
  --bucket http://storage:8000/metastore \
  "$META_URL"  experiment

mkdir -p /mnt/metastore/experiment
juicefs mount "$META_URL" /mnt/metastore/experiment -d

echo "Checking if Aim repo exists"

# Initialise repo if new
if [[ ! -d /mnt/metastore/experiment/.aim ]]; then
  echo "Aim repo does not exist creating a new one"
  aim init --repo /mnt/metastore/experiment
fi

echo "Starting Aim"

# Start Aim
aim server  \
    --repo /mnt/metastore/experiment \
    --host 0.0.0.0 --port 53800 &

server_pid=$!

aim up \
    --repo /mnt/metastore/experiment \
    --host 0.0.0.0 --port 43800 \
    --base-path /experiment-tracker