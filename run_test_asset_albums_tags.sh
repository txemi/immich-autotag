#!/bin/bash
# Script to run immich_api_example_read_asset_tags_albums.py in the correct virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON_SCRIPT="$PROJECT_ROOT/immich_api_example_read_asset_tags_albums.py"

if [ ! -d "$VENV_DIR" ]; then
  echo "[ERROR] Virtual environment not found in $VENV_DIR"
  echo "Please create the virtual environment and make sure to install the required dependencies."
  exit 1
fi

source "$VENV_DIR/bin/activate"
python "$PYTHON_SCRIPT"
deactivate
