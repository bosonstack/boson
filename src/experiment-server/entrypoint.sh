#!/bin/bash
set -e

# Configure S3FS
echo ${STORAGE_USER}:${STORAGE_PASSWORD} > /root/.passwd-s3fs
chmod 600 /root/.passwd-s3fs

s3fs metastore /mnt/metastore \
     -o url=http://storage:8000 \
     -o use_path_request_style \
     -o allow_other \
     -o passwd_file=/root/.passwd-s3fs \
     -o uid="$(id -u)" \
     -o gid="$(id -g)" \
     -o nonempty \
     -o curldbg -o dbglevel=info \
     -o logfile=/var/log/s3fs-metastore.log

mkdir -p /mnt/metastore/experiments

# Initialise repo if new
if [[ ! -d /mnt/metastore/experiments/.aim ]]; then
  aim init --repo /mnt/metastore/experiments
fi

aim server  \
    --repo /mnt/metastore/experiments \
    --host 0.0.0.0 --port 53800 &

server_pid=$!

aim up \
    --repo /mnt/metastore/experiments \
    --host 0.0.0.0 --port 43800 \
    --base-path /experiment-tracker \
    --log-level debug