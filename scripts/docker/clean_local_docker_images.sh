#!/bin/bash
# clean_local_docker_images.sh
# Removes all local Docker images related to immich-autotag (one-shot and cron)
# Usage: bash scripts/docker/clean_local_docker_images.sh
set -euo pipefail

# List all immich-autotag images before deletion
ALL_IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^txemi/immich-autotag' || true)

if [ -z "$ALL_IMAGES" ]; then
  echo "[INFO] No local immich-autotag images found before cleanup."
else
  echo "[INFO] Local immich-autotag images before cleanup:"
  echo "$ALL_IMAGES"
fi

# Select images to delete
IMAGES_TO_DELETE="$ALL_IMAGES"

if [ -z "$IMAGES_TO_DELETE" ]; then
  echo "[INFO] Nothing to delete."
else
  echo "[INFO] Removing the following images:"
  echo "$IMAGES_TO_DELETE"
  docker rmi -f $IMAGES_TO_DELETE || true
fi

# List all immich-autotag images after deletion
REMAINING_IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^txemi/immich-autotag' || true)

if [ -z "$REMAINING_IMAGES" ]; then
  echo "[OK] All immich-autotag images removed. No images remain."
else
  echo "[WARN] Some immich-autotag images remain after cleanup:"
  echo "$REMAINING_IMAGES"
fi
