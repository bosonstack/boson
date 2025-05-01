#!/bin/bash
set -e

mkdir -p /mnt/metastore

echo "${STORAGE_USER}:${STORAGE_PASSWORD}" > /root/.passwd-s3fs
chmod 600 /root/.passwd-s3fs

s3fs metastore /mnt/metastore \
    -o url=http://storage:${STORAGE_PORT} \
    -o use_path_request_style \
    -o passwd_file=/root/.passwd-s3fs \
    -o nonempty \
    -o allow_other \
    -o endpoint=storage

mkdir -p /mnt/metastore/workspace
