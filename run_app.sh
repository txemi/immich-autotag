#!/bin/bash
# Activates the virtual environment and runs the main entry point of the Immich app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"

if [ ! -d "$VENV_DIR" ]; then
  echo "ERROR: Virtual environment not found in $VENV_DIR"
  exit 1
fi

source "$VENV_DIR/bin/activate"

python "$PYTHON_SCRIPT" "$@"
