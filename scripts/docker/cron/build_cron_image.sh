#!/bin/bash
# Build the cron-enabled Docker image for Immich AutoTag
set -e

REPO_ROOT="$(cd "$(dirname "$0")/../../../" && pwd)"
cd "$REPO_ROOT"
# Get version and hash
VERSION=$(grep '^version' "$REPO_ROOT/pyproject.toml" | head -1 | cut -d'=' -f2 | tr -d ' "')
HASH=$(git rev-parse --short HEAD)

IMAGE_CRON="txemi/immich-autotag:cron"
IMAGE_CRON_VERSION="txemi/immich-autotag:cron-$VERSION"
IMAGE_CRON_VERSION_HASH="txemi/immich-autotag:cron-$VERSION-$HASH"

docker build -f "$REPO_ROOT/Dockerfile.cron" -t $IMAGE_CRON -t $IMAGE_CRON_VERSION -t $IMAGE_CRON_VERSION_HASH "$REPO_ROOT"
echo -e "\nBuilt images: $IMAGE_CRON, $IMAGE_CRON_VERSION, $IMAGE_CRON_VERSION_HASH"
