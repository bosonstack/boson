#!/bin/bash
set -e

echo "🚀 Launching Jupyter..."
exec poetry run jupyter server --config=/root/.jupyter/jupyter_notebook_config.py --ip=0.0.0.0 --port=8888 --no-browser --allow-root --debug