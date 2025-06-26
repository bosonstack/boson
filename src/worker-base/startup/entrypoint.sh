#!/usr/bin/env bash
set -e

# # Configure S3FS
echo ${STORAGE_USER}:${STORAGE_PASSWORD} > /root/.passwd-s3fs
chmod 600 /root/.passwd-s3fs
s3fs metastore /mnt/metastore \
     -o url="${STORAGE_ENDPOINT}" \
     -o use_path_request_style \
     -o allow_other \
     -o passwd_file=/root/.passwd-s3fs \
     -o uid="$(id -u)" \
     -o gid="$(id -g)" \
     -o nonempty \
     -o curldbg -o dbglevel=info \
     -o logfile=/var/log/s3fs-metastore.log
mkdir -p /mnt/metastore/workspace

cd /mnt/metastore/workspace
python -m ipykernel_launcher -f /tmp/connection.json &
KERNEL_PID=$!

trap 'kill -TERM $KERNEL_PID 2>/dev/null' TERM INT

exec python /root/watchdog.py --kernel-pid "$KERNEL_PID"