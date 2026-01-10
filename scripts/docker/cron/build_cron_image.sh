#!/bin/bash
# Build the cron-enabled Docker image for Immich AutoTag
set -e
REPO_ROOT="$(cd "$(dirname "$0")/../../../" && pwd)"
cd "$REPO_ROOT"
docker build -f "$REPO_ROOT/Dockerfile.cron" -t txemi/immich-autotag:cron "$REPO_ROOT"
echo -e "\nBuilt image: txemi/immich-autotag:cron"
