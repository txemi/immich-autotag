#!/bin/bash
# Cleans all .pyc files and __pycache__ folders in the project

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -type f -delete

echo "Cleanup of .pyc files and __pycache__ folders completed."
