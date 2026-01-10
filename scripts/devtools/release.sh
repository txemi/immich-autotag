#!/bin/bash
# release.sh
# Script maestro para publicar una nueva versión de immich-autotag
# Uso: bash scripts/devtools/release.sh <nueva_version>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: $0 <nueva_version>"
  exit 1
fi

NEW_VERSION="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
CHECK_SCRIPT="$PROJECT_ROOT/scripts/devtools/check_versions.sh"
UPDATE_SCRIPT="$PROJECT_ROOT/scripts/devtools/update_version_info.sh"

# 1. Actualizar pyproject.toml
sed -i "s/^version = .*/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
echo "[INFO] pyproject.toml actualizado a versión $NEW_VERSION"

git add "$PYPROJECT_TOML"
git commit -m "Bump version to $NEW_VERSION"

# 2. Crear tag git
TAG="v$NEW_VERSION"
git tag "$TAG"
echo "[INFO] Tag git creado: $TAG"

# 3. Chequear consistencia
bash "$CHECK_SCRIPT"
echo "[INFO] Chequeo de versiones OK"

# 4. Actualizar versión en el código
bash "$UPDATE_SCRIPT"
echo "[INFO] version.py actualizado"

git add "$PROJECT_ROOT/immich_autotag/version.py"
git commit -m "Update version info for $NEW_VERSION"

git push
# Si quieres subir el tag también:
git push origin "$TAG"

echo "Release $NEW_VERSION completado. Todo sincronizado."
