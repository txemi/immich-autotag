#!/bin/bash
# full_release.sh
#
# PURPOSE: Complete release pipeline - version + PyPI + Docker (all-in-one)
#
# WHAT IT DOES:
#   1. Calls release.sh (version bump + git tagging)
#   2. Builds and publishes to TestPyPI (for validation)
#   3. Builds and publishes to PyPI (production Python package)
#   4. Builds and pushes Docker images to Docker Hub (main + cron variants)
#
# WHAT IT REQUIRES:
#   - PyPI credentials configured (via token or .pypirc)
#   - Docker Hub credentials configured (via ~/.docker/config.json)
#   - Git push access to origin
#
# USE WHEN:
#   - You are ready for a public release
#   - Version is stable and tested
#   - You want everything published at once
#   - Never use this on experimental/development versions
#
# USAGE: bash scripts/devtools/full_release.sh <new_version>
# EXAMPLE: bash scripts/devtools/full_release.sh 0.72.0
#
# WARNING: This script performs PUBLIC pushes. Use with caution!
#
set -euo pipefail
set -x

if [ $# -ne 1 ]; then
  echo "Usage: $0 <new_version>"
  exit 1
fi

NEW_VERSION="$1"

# Detect project root robustly (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/../..")"
cd "$PROJECT_ROOT"

# 1. Run the release script (bumps version, commits, tags, updates version.py, pushes)
bash "$PROJECT_ROOT/scripts/devtools/release.sh" "$NEW_VERSION"


# 2. Ensure virtual environment and dependencies are ready
bash "$PROJECT_ROOT/setup_venv.sh"

# 3. Upload to TestPyPI
bash "$PROJECT_ROOT/scripts/pypi/package_and_upload.sh" --test

# 4. Upload to PyPI
bash "$PROJECT_ROOT/scripts/pypi/package_and_upload.sh"

# 4. Build and push one-shot Docker image
bash "$PROJECT_ROOT/scripts/docker/one_shot/build_and_push.sh"

# 5. Build and push cron Docker image
bash "$PROJECT_ROOT/scripts/docker/cron/build_cron_image.sh"
bash "$PROJECT_ROOT/scripts/docker/cron/push_cron_image.sh"

echo "[OK] Full release and deployment completed for version $NEW_VERSION."

# Print direct links for quick manual review

PACKAGE_NAME="immich-autotag"
DOCKERHUB_USER="txemi"

echo "\n[INFO] Quick review links for version $NEW_VERSION:"
echo "PyPI:        https://pypi.org/project/$PACKAGE_NAME/$NEW_VERSION/"
echo "TestPyPI:    https://test.pypi.org/project/$PACKAGE_NAME/$NEW_VERSION/"
echo "Docker Hub (one-shot): https://hub.docker.com/r/$DOCKERHUB_USER/$PACKAGE_NAME/tags?page=1&name=$NEW_VERSION"
echo "Docker Hub (cron):     https://hub.docker.com/r/$DOCKERHUB_USER/$PACKAGE_NAME/tags?page=1&name=cron-$NEW_VERSION"
echo "PyPI history:     https://pypi.org/project/$PACKAGE_NAME/#history"
echo "TestPyPI history: https://test.pypi.org/project/$PACKAGE_NAME/#history"