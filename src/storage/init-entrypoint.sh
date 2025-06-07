#!/bin/bash
set -e

# Wait for S3 service to become available
until aws --endpoint-url http://storage:8000 s3api list-buckets > /dev/null 2>&1; do
  echo "Waiting for storage service..."
  sleep 2
done

echo "Storage service is ready. Creating bucket..."

aws --endpoint-url http://storage:8000 s3api create-bucket --bucket metastore
aws --endpoint-url http://storage:8000 s3api put-bucket-versioning --bucket metastore --versioning-configuration Status=Enabled
