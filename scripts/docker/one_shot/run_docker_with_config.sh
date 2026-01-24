#!/bin/bash

# Portable script to start the Docker container of immich-autotag mounting config
# Usage: bash scripts/run_docker_with_config.sh [--image imagename] <local_config_path> [docker_options]

set -euo pipefail
set -x

# Default image name (local build)
DEFAULT_IMAGE_NAME="immich-autotag:latest"

# Parse --image argument or IMAGE_NAME environment variable
IMAGE_NAME="$DEFAULT_IMAGE_NAME"
if [ -n "${IMAGE_NAME_OVERRIDE:-}" ]; then
	IMAGE_NAME="$IMAGE_NAME_OVERRIDE"
fi
if [ "$1" = "--image" ]; then
	shift
	IMAGE_NAME="$1"
	shift
fi
if [ -n "$IMAGE_NAME" ]; then
	: # IMAGE_NAME is already configured
elif [ -n "$IMAGE_NAME" ]; then
	: # fallback
else
	IMAGE_NAME="$DEFAULT_IMAGE_NAME"
fi

# The container user is autotaguser, their home is /home/autotaguser
CONTAINER_CONFIG_DIR="/home/autotaguser/.config/immich_autotag"

# Calculate repository root (three levels up from one_shot)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Output directory
HOST_OUTPUT_DIR="$REPO_ROOT/logs_docker_one_shot"
CONTAINER_OUTPUT_DIR="/home/autotaguser/logs"

# Create output directory if it doesn't exist and ensure write permissions
mkdir -p "$HOST_OUTPUT_DIR"
chmod -R 777 "$HOST_OUTPUT_DIR"

# If an argument is passed, use it as config path
if [ $# -ge 1 ]; then
	CONFIG_LOCAL_PATH="$1"
	shift
else
	# Automatically search in typical paths
	# 1. Development: user_config.py/yaml in <repo_root>/immich_autotag/config/
	if [ -f "$REPO_ROOT/immich_autotag/config/user_config.py" ]; then
		CONFIG_LOCAL_PATH="$REPO_ROOT/immich_autotag/config/user_config.py"
	elif [ -f "$REPO_ROOT/immich_autotag/config/user_config.yaml" ]; then
		CONFIG_LOCAL_PATH="$REPO_ROOT/immich_autotag/config/user_config.yaml"
	# 2. Home config: ~/.config/immich_autotag/config.py/yaml
	elif [ -f "$HOME/.config/immich_autotag/config.py" ]; then
		CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag/config.py"
	elif [ -f "$HOME/.config/immich_autotag/config.yaml" ]; then
		CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag/config.yaml"
	# 3. Legacy: ~/.immich_autotag/config.py/yaml
	elif [ -f "$HOME/.immich_autotag/config.py" ]; then
		CONFIG_LOCAL_PATH="$HOME/.immich_autotag/config.py"
	elif [ -f "$HOME/.immich_autotag/config.yaml" ]; then
		CONFIG_LOCAL_PATH="$HOME/.immich_autotag/config.yaml"
	# 4. Complete directory (development)
	elif [ -d "$REPO_ROOT/immich_autotag/config" ]; then
		CONFIG_LOCAL_PATH="$REPO_ROOT/immich_autotag/config"
	# 5. Complete directory (home)
	elif [ -d "$HOME/.config/immich_autotag" ]; then
		CONFIG_LOCAL_PATH="$HOME/.config/immich_autotag"
	elif [ -d "$HOME/.immich_autotag" ]; then
		CONFIG_LOCAL_PATH="$HOME/.immich_autotag"
	else
		echo "ERROR: Configuration not found in typical paths."
		echo "You can pass the path as an argument: $0 <local_config_path> [docker_options]"
		exit 1
	fi
fi

# Convert config path to absolute
CONFIG_ABS_PATH="$(realpath "$CONFIG_LOCAL_PATH")"

# Build volume options (config and fixed output)
VOLUMES=""
if [ -d "$CONFIG_ABS_PATH" ]; then
	echo "Mounting configuration directory: $CONFIG_ABS_PATH -> $CONTAINER_CONFIG_DIR"
	VOLUMES+="-v $CONFIG_ABS_PATH:$CONTAINER_CONFIG_DIR "
elif [ -f "$CONFIG_ABS_PATH" ]; then
	EXT="${CONFIG_ABS_PATH##*.}"
	if [ "$EXT" = "yaml" ] || [ "$EXT" = "yml" ]; then
		DEST="$CONTAINER_CONFIG_DIR/config.yaml"
	elif [ "$EXT" = "py" ]; then
		DEST="$CONTAINER_CONFIG_DIR/config.py"
	else
		echo "ERROR: File must be .yaml, .yml or .py"
		exit 2
	fi
	echo "Mounting configuration file: $CONFIG_ABS_PATH -> $DEST"
	VOLUMES+="-v $CONFIG_ABS_PATH:$DEST "
else
	echo "ERROR: $CONFIG_ABS_PATH does not exist"
	exit 3
fi

# Always mount fixed output directory
echo "Mounting output directory: $HOST_OUTPUT_DIR -> $CONTAINER_OUTPUT_DIR"
VOLUMES+="-v $HOST_OUTPUT_DIR:$CONTAINER_OUTPUT_DIR "

docker run --rm $VOLUMES "$IMAGE_NAME" "$@"
