#!/bin/bash
# venv_launcher.sh: Launches a Python script using the project's virtualenv, regardless of where it is called from.
# Usage: ./venv_launcher.sh <python_script> [args...]

set -e
set -o pipefail

# Locate the project root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PY="$REPO_ROOT/.venv/bin/python"

# Add the repo root to PYTHONPATH for absolute imports
export PYTHONPATH="$REPO_ROOT"

if [ ! -x "$VENV_PY" ]; then
	echo "[FATAL] Virtualenv not found at $VENV_PY" >&2
	exit 2
fi


# If no script is provided, default to main.py in this directory
if [ $# -lt 1 ]; then
	PY_SCRIPT="$SCRIPT_DIR/main.py"
else
	PY_SCRIPT="$1"
	shift
fi

exec "$VENV_PY" "$PY_SCRIPT" "$@"
