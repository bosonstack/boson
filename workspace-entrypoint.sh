#!/bin/bash
set -e

# Mount S3
echo "🔧 Mounting cloud storage..."
/root/.mount-cloud-storage.sh

# Wait for target dir to appear
echo "⏳ Waiting for /mnt/metastore/workspace..."
while [ ! -d "/mnt/metastore/workspace" ]; do
  sleep 0.5
done

echo "🚀 Launching Jupyter..."
exec poetry run jupyter server --config=/root/.jupyter/jupyter_notebook_config.py --ip=0.0.0.0 --port=8888 --no-browser --allow-root
