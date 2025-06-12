#!/bin/bash
set -e

echo "🚀 Launching Jupyter..."
exec python -m jupyter_server \
     --config=/root/.jupyter/jupyter_notebook_config.py \
     --ip=0.0.0.0 \
     --port=8888 \
     --no-browser \
     --allow-root \
     --debug