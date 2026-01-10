#!/bin/bash
set -euo pipefail
# Build and push the Docker image to Docker Hub with both 'latest' and version tags

# Detect repo root (three levels up from one_shot)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Get version from pyproject.toml
VERSION=$(grep '^version' "$REPO_ROOT/pyproject.toml" | head -1 | cut -d'=' -f2 | tr -d ' "')

IMAGE_NAME_LATEST="txemi/immich-autotag:latest"
IMAGE_NAME_VERSION="txemi/immich-autotag:$VERSION"

echo "[INFO] Building Docker image: $IMAGE_NAME_LATEST and $IMAGE_NAME_VERSION"
docker build -t $IMAGE_NAME_LATEST -t $IMAGE_NAME_VERSION "$REPO_ROOT"

echo "[INFO] Pushing image to Docker Hub: $IMAGE_NAME_LATEST"
docker push $IMAGE_NAME_LATEST
echo "[INFO] Pushing image to Docker Hub: $IMAGE_NAME_VERSION"
docker push $IMAGE_NAME_VERSION

echo "[OK] Images built and pushed successfully."
echo "[INFO] View your images at: https://hub.docker.com/r/txemi/immich-autotag/tags"
