#!/usr/bin/env bash
 # Script to move immich_client to project root, build and upload to PyPI/TestPyPI, then restore folder
 # Usage: ./scripts/pypi/package_and_upload.sh


set -euo pipefail
set -x

# --- Ensure venv and client are ready ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/../..")"
cd "$PROJECT_ROOT"

# Call setup_venv.sh if it exists
if [ -f "$PROJECT_ROOT/setup_venv.sh" ]; then
  echo "[INFO] Running setup_venv.sh to ensure venv and client are ready..."
  bash "$PROJECT_ROOT/setup_venv.sh"
else
  echo "[WARN] setup_venv.sh not found, proceeding without it."
fi

 # --- Optionally increment patch number in pyproject.toml ---
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
AUTO_INCREMENT_PATCH="false"
if [ "${AUTO_INCREMENT_PATCH}" = "true" ]; then
  if [ -f "$PYPROJECT_TOML" ]; then
    VERSION_LINE=$(grep '^version' "$PYPROJECT_TOML")
    VERSION=$(echo "$VERSION_LINE" | cut -d'=' -f2 | tr -d ' "')
    IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"
    NEW_PATCH=$((PATCH + 1))
    NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
    # Replace version line
    sed -i "s/^version = .*/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
    echo "[INFO] Version automatically incremented: $VERSION -> $NEW_VERSION"
  fi
else
  echo "[INFO] Patch auto-increment is disabled. Version in pyproject.toml will be used as-is."
fi

 # Check and activate standard virtual environment if exists and not active
if [ -z "${VIRTUAL_ENV:-}" ] || [ "$(basename "$VIRTUAL_ENV")" != ".venv" ]; then
  if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "[INFO] Activating .venv virtual environment..."
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.venv/bin/activate"
  else
    echo "[ERROR] .venv virtual environment not found in $PROJECT_ROOT. Please create it with 'python3 -m venv .venv' and try again."
    exit 1
  fi
fi

IMMICH_CLIENT_ORIG="$PROJECT_ROOT/immich-client/immich_client"
IMMICH_CLIENT_DEST="$PROJECT_ROOT/immich_client"
IMMICH_CLIENT_BACKUP="$PROJECT_ROOT/immich-client/immich_client_backup_$(date +%s)"


 # Only move if destination does not exist and origin does
if [ ! -d "$IMMICH_CLIENT_DEST" ] && [ -d "$IMMICH_CLIENT_ORIG" ]; then
  mv "$IMMICH_CLIENT_ORIG" "$IMMICH_CLIENT_DEST"
elif [ -d "$IMMICH_CLIENT_DEST" ]; then
  echo "$IMMICH_CLIENT_DEST is already at root, not moving."
else
  echo "$IMMICH_CLIENT_ORIG and $IMMICH_CLIENT_DEST not found. Aborting."
  exit 1
fi


 # Build the package
 # Clean dist/ folder before building
if [ -d dist ]; then
  rm -rf dist/*
fi

 # Install build if not present in virtual environment
if ! python3 -m build --version &> /dev/null; then
  echo "[INFO] Installing build in virtual environment..."
  pip install build
fi

python3 -m build

 # Upload to PyPI/TestPyPI

 # Install twine in virtual environment if not present
if ! command -v twine &> /dev/null; then
  echo "[INFO] twine is not installed. Installing in virtual environment..."
  pip install twine
fi

REPO="pypi"
for arg in "$@"; do
  if [ "$arg" = "--test" ] || [ "$arg" = "-t" ]; then
    REPO="testpypi"
  fi
done

echo "[INFO] Uploading to repository: $REPO"
twine upload --repository "$REPO" dist/*

# Print direct verification URL
PKG_NAME="immich-client"
if [ -f "$PYPROJECT_TOML" ]; then
  VERSION_LINE=$(grep '^version' "$PYPROJECT_TOML")
  VERSION=$(echo "$VERSION_LINE" | cut -d'=' -f2 | tr -d ' "')
  if [ "$REPO" = "testpypi" ]; then
    echo "[INFO] Verify your package at: https://test.pypi.org/project/$PKG_NAME/$VERSION/"
  else
    echo "[INFO] Verify your package at: https://pypi.org/project/$PKG_NAME/$VERSION/"
  fi
fi


 # Only restore if destination exists and origin does not
if [ -d "$IMMICH_CLIENT_DEST" ] && [ ! -d "$IMMICH_CLIENT_ORIG" ]; then
  mv "$IMMICH_CLIENT_DEST" "$IMMICH_CLIENT_ORIG"
else
  echo "No need to restore $IMMICH_CLIENT_DEST."
fi

echo "Operation completed."
