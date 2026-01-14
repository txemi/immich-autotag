#!/bin/bash
# release.sh
# Master script to release a new version of immich-autotag
# Usage: bash scripts/devtools/release.sh <new_version>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: $0 <new_version>"
  exit 1
fi

NEW_VERSION="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
CHECK_SCRIPT="$PROJECT_ROOT/scripts/devtools/check_versions.sh"
UPDATE_SCRIPT="$PROJECT_ROOT/scripts/devtools/update_version_info.sh"

# 1. Update pyproject.toml
sed -i "s/^version = .*/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
echo "[INFO] pyproject.toml updated to version $NEW_VERSION"

# 2. Update version in code
bash "$UPDATE_SCRIPT"
echo "[INFO] version.py updated"

# 3. Check consistency
bash "$CHECK_SCRIPT"
echo "[INFO] Version check OK"

# 4. Commit all version changes together
git add "$PYPROJECT_TOML" "$PROJECT_ROOT/immich_autotag/version.py"
git commit -m "Bump version to $NEW_VERSION"

# 5. Create git tag (AFTER all version updates are committed)
TAG="v$NEW_VERSION"
git tag "$TAG"
echo "[INFO] Git tag created: $TAG"

# 6. Update version.py again to capture the new tag in git describe
bash "$UPDATE_SCRIPT"
echo "[INFO] version.py updated with new tag information"

git add "$PROJECT_ROOT/immich_autotag/version.py"
git commit -m "Update version.py with tag $TAG information"

# 7. Push everything
git push
git push origin "$TAG"

echo "Release $NEW_VERSION completed. Everything synchronized."
