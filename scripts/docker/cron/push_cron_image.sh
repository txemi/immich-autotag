#!/bin/bash
# Push all versioned cron Docker images to Docker Hub
set -e
REPO_ROOT="$(cd "$(dirname "$0")/../../../" && pwd)"
VERSION=$(grep '^version' "$REPO_ROOT/pyproject.toml" | head -1 | cut -d'=' -f2 | tr -d ' "')
HASH=$(git -C "$REPO_ROOT" rev-parse --short HEAD)

docker push txemi/immich-autotag:cron
docker push txemi/immich-autotag:cron-$VERSION
docker push txemi/immich-autotag:cron-$VERSION-$HASH

echo "\nPushed images: txemi/immich-autotag:cron, txemi/immich-autotag:cron-$VERSION, txemi/immich-autotag:cron-$VERSION-$HASH"
echo "[INFO] View your images at: https://hub.docker.com/r/txemi/immich-autotag/tags"
