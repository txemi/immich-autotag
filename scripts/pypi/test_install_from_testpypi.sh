#!/usr/bin/env bash
# Script to test installation from TestPyPI in a clean environment
# Usage: ./scripts/pypi/test_install_from_testpypi.sh

set -euo pipefail

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- Argument parsing ---
PYPROJECT_TOML="$REPO_ROOT/pyproject.toml"
PKG_NAME="immich-autotag"
# Default version: from pyproject.toml
PKG_VERSION=$(grep '^version' "$PYPROJECT_TOML" | head -n1 | cut -d'=' -f2 | tr -d ' "')
# Default repo: PyPI
REPO="pypi"

if [ $# -ge 1 ]; then
	PKG_VERSION="$1"
fi
if [ $# -ge 2 ]; then
	REPO="$2"
fi

TEMP_DIR="$REPO_ROOT/temp_install_test"
rm -rf "$TEMP_DIR"
mkdir "$TEMP_DIR"
cd "$TEMP_DIR"

# Create and activate clean virtual environment
python3 -m venv venv-test
source venv-test/bin/activate

if [ "$REPO" = "testpypi" ]; then
	echo "[INFO] Installing from TestPyPI: version $PKG_VERSION"
	pip install --index-url https://test.pypi.org/simple/ \
		--extra-index-url https://pypi.org/simple/ \
		--no-cache-dir --upgrade "$PKG_NAME==$PKG_VERSION"
else
	echo "[INFO] Installing from PyPI: version $PKG_VERSION"
	pip install --no-cache-dir --upgrade "$PKG_NAME==$PKG_VERSION"
fi

# Test importing the generated client
python -c "import immich_client; print('Successful import of immich_client')"

# Test CLI if it exists
if command -v "$PKG_NAME" &>/dev/null; then
	echo "Testing CLI:"
	"$PKG_NAME" --help
else
	echo "CLI command '$PKG_NAME' not found."
fi

# Exit virtual environment and cleanup
deactivate
cd "$REPO_ROOT"
rm -rf "$TEMP_DIR"

echo "Installation test completed in clean environment."
