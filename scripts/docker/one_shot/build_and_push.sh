#!/bin/bash
set -euo pipefail
# Build and push the Docker image to Docker Hub
# Usage: bash build_and_push.sh

IMAGE_NAME="txemi/immich-autotag:latest"

 # Detect repo root (three levels up from one_shot)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "[INFO] Building Docker image: $IMAGE_NAME"
docker build -t $IMAGE_NAME "$REPO_ROOT"

echo "[INFO] Pushing image to Docker Hub: $IMAGE_NAME"
docker push $IMAGE_NAME


echo "[OK] Image built and pushed successfully."
echo "[INFO] View your image at: https://hub.docker.com/r/txemi/immich-autotag/tags"
