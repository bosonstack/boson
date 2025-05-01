#!/bin/bash

# Validate arguments
if [ $# -ne 2 ]; then
  echo "Usage: $0 <WORKSPACE_NAME_NO_HYPHENS_OR_UNDERSCORES> <PORT>"
  exit 1
fi

WORKSPACE_NAME="$1"
PORT="$2"

# Check for invalid characters in the workspace name
if [[ "$WORKSPACE_NAME" == *"-"* || "$WORKSPACE_NAME" == *"_"* ]]; then
  echo "Error: Workspace name cannot contain hyphens (-) or underscores (_)."
  exit 1
fi

SRC_WORKSPACE="example-instacart"
SRC_DIR="workspaces/$SRC_WORKSPACE"
DEST_DIR="workspaces/$WORKSPACE_NAME"

# Step 1: Copy workspace
if [ -d "$DEST_DIR" ]; then
  echo "Error: Destination workspace '$DEST_DIR' already exists."
  exit 1
fi

cp -r "$SRC_DIR" "$DEST_DIR"

# Step 2: Replace in docker-compose.override.yml
DOCKER_COMPOSE="$DEST_DIR/docker-compose.override.yml"
sed -i "s/example-instacart/$WORKSPACE_NAME/g" "$DOCKER_COMPOSE"
sed -i "s/example_instacart/${WORKSPACE_NAME}/g" "$DOCKER_COMPOSE"
sed -i "s/Example - Instacart/$WORKSPACE_NAME/g" "$DOCKER_COMPOSE"

# Step 3: Replace in pyproject.toml
PYPROJECT="$DEST_DIR/pyproject.toml"
sed -i "s/example-instacart/$WORKSPACE_NAME/g" "$PYPROJECT"
sed -i "s/Example - Instacart/$WORKSPACE_NAME/g" "$PYPROJECT"

# Step 4: Set port in .env
ENV_FILE="$DEST_DIR/.env"
if grep -q "^PORT=" "$ENV_FILE"; then
  sed -i "s/^PORT=.*/PORT=$PORT/" "$ENV_FILE"
else
  echo "PORT=$PORT" >> "$ENV_FILE"
fi

echo "Workspace '$WORKSPACE_NAME' created with port $PORT."
