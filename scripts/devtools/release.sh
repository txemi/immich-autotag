#!/bin/bash
# release.sh
#
# PURPOSE: Version bump + Git tagging ONLY (no PyPI/Docker publishing)
#
# WHAT IT DOES:
#   1. Updates version in pyproject.toml
#   2. Updates version.py with new version and git describe
#   3. Creates git tag (v{version})
#   4. Commits version changes
#   5. Pushes tag and commits to origin
#
# WHAT IT DOES NOT DO:
#   - Does not publish to PyPI
#   - Does not build/push Docker images
#   - Does not run tests
#
# USE WHEN:
#   - You want to prepare a release for review/testing
#   - You want to tag intermediate checkpoints in the changelog
#   - You will manually decide later whether to publish or just keep the tag
#
# USAGE: bash scripts/devtools/release.sh <new_version>
# EXAMPLE: bash scripts/devtools/release.sh 0.72.0
#
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

# 2. Update version in code (will have old tag info initially)
bash "$UPDATE_SCRIPT"
echo "[INFO] version.py updated"

# 3. Commit all version changes together
git add "$PYPROJECT_TOML" "$PROJECT_ROOT/immich_autotag/version.py"
git commit -m "Bump version to $NEW_VERSION"

# 4. Create git tag (AFTER all version updates are committed)
TAG="v$NEW_VERSION"
git tag "$TAG"
echo "[INFO] Git tag created: $TAG"

# 5. Update version.py again to capture the new tag in git describe
bash "$UPDATE_SCRIPT"
echo "[INFO] version.py updated with new tag information"

git add "$PROJECT_ROOT/immich_autotag/version.py"
git commit -m "Update version.py with tag $TAG information"

# 6. Check consistency (now tag and version should match)
bash "$CHECK_SCRIPT"
echo "[INFO] Version check OK"

# 7. Push everything
git push
git push origin "$TAG"

echo "Release $NEW_VERSION completed. Everything synchronized."
