#!/bin/bash
# clean_local_docker_images.sh
# Removes all local Docker images related to immich-autotag (one-shot and cron)
# Usage: bash scripts/docker/clean_local_docker_images.sh
set -euo pipefail

IMAGES=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^txemi/immich-autotag')

if [ -z "$IMAGES" ]; then
  echo "[INFO] No local immich-autotag images found."
  exit 0
fi

echo "[INFO] Removing the following images:"
echo "$IMAGES"
docker rmi -f $IMAGES

echo "[OK] All local immich-autotag images removed."
