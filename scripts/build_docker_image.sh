#!/bin/bash
set -e

# Build the Docker image
docker build -t immich-autotag:latest .

# (Optional) Show the image just built
docker images | grep immich-autotag

# Run the CLI help to verify the image works
docker run --rm immich-autotag:latest --help
