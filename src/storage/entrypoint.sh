#!/bin/sh
set -e

export AWS_ACCESS_KEY_ID="${STORAGE_USER}"
export AWS_SECRET_ACCESS_KEY="${STORAGE_PASSWORD}"
export SCALITY_ACCESS_KEY_ID="${STORAGE_USER}"
export SCALITY_SECRET_ACCESS_KEY="${STORAGE_PASSWORD}"

echo "Launching Zenko CloudServer..."
/usr/src/app/docker-entrypoint.sh "$@" &
pid=$!

until aws --endpoint-url http://storage:8000 s3api list-buckets; do
  echo "Waiting for storage endpoint to be live..."
  sleep 2
done

echo "Creating bucket..."
aws --endpoint-url http://storage:8000 s3api create-bucket --bucket metastore || true
aws --endpoint-url http://storage:8000 s3api put-bucket-versioning \
  --bucket metastore \
  --versioning-configuration Status=Enabled

echo "Created bucket, ready for connections..."
trap "kill -TERM $pid" TERM INT
wait $pid
