#!/bin/bash
# update_version_info.sh
# Updates immich_autotag/version.py with the version from pyproject.toml and git commit
set -e
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
VERSION=$(grep '^version' "$PYPROJECT_TOML" | head -1 | cut -d'=' -f2 | tr -d ' "')
GIT_COMMIT=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD)
GIT_DESCRIBE=$(git -C "$PROJECT_ROOT" describe --tags --always --long --dirty)
VERSION_FILE="$PROJECT_ROOT/immich_autotag/version.py"
echo "# This file is automatically updated in the build/distribution process" >"$VERSION_FILE"
echo "__version__ = \"$VERSION\"" >>"$VERSION_FILE"
echo "__git_commit__ = \"$GIT_COMMIT\"" >>"$VERSION_FILE"
echo "__git_describe__ = \"$GIT_DESCRIBE\"" >>"$VERSION_FILE"
echo "Updated $VERSION_FILE: version=$VERSION, commit=$GIT_COMMIT, describe=$GIT_DESCRIBE"
