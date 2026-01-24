#!/bin/bash
# Run immich-autotag using the public Docker image from Docker Hub
# Usage: bash scripts/docker/run_docker_public.sh [config_path] [docker_options]

SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"
"$SCRIPT_DIR/run_docker_with_config.sh" --image txemi/immich-autotag:latest "$@"
