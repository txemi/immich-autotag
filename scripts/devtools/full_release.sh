
#!/bin/bash
# full_release.sh
# Script to automate version bump, release, and deployment to PyPI, TestPyPI, and Docker Hub (one-shot and cron images)
# Usage: bash scripts/devtools/full_release.sh <new_version>
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

# 2. Upload to TestPyPI
bash "$PROJECT_ROOT/scripts/pypi/package_and_upload.sh" --test

# 3. Upload to PyPI
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