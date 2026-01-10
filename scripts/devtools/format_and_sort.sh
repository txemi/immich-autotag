#!/bin/bash
# Script to format and organize imports in the project, avoiding .venv and external libraries
set -x
set -e

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_NAME="immich_autotag"

# Move to repo root
cd "$REPO_ROOT"

# Directory to format (default: main package folder)
TARGET_DIR="${1:-$PACKAGE_NAME}"

# Robust exclusions to avoid formatting .venv and other external directories
BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"
ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts"

# Activate project virtual environment robustly
VENV_PATH="$REPO_ROOT/.venv/bin/activate"
if [ ! -f "$VENV_PATH" ]; then
	echo "[ERROR] Virtual environment not found at $VENV_PATH"
	echo "First run the setup script: bash setup_venv.sh"
	exit 1
fi

source "$VENV_PATH"

# Install black and isort if not available
if ! "$REPO_ROOT/.venv/bin/python" -c "import black" 2>/dev/null; then
	echo "Installing black in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install black
fi
if ! "$REPO_ROOT/.venv/bin/python" -c "import isort" 2>/dev/null; then
	echo "Installing isort in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install isort
fi

# Format code with Black using the virtual environment Python
"$REPO_ROOT/.venv/bin/python" -m black $BLACK_EXCLUDES "$TARGET_DIR"

# Organize imports with isort using the virtual environment Python
"$REPO_ROOT/.venv/bin/python" -m isort $ISORT_SKIPS "$TARGET_DIR"

echo "Formatting and import sorting completed."
