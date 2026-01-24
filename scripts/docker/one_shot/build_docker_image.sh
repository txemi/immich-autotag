#!/bin/bash
set -e

# Calculate repository root (three levels up from one_shot)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Build the Docker image
docker build -t immich-autotag:latest "$REPO_ROOT"

# (Optional) Show the image just built
docker images | grep immich-autotag

# Run the CLI help to verify the image works
docker run --rm immich-autotag:latest --help
