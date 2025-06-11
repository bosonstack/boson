#!/bin/bash
set -e

poetry lock --directory ./src/common-lib/flint/
poetry lock --directory ./src/catalog-explorer/
poetry lock --directory ./src/kernel/
poetry lock --directory ./src/workspace/

echo "Updated Common Lib and its dependent services."