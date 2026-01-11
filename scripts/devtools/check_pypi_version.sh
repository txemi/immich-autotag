#!/usr/bin/env bash
# check_pypi_version.sh
# Verifica que la versión de version.py local coincide con la publicada en PyPI (wheel)
# Uso: ./check_pypi_version.sh [version]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCAL_VERSION_FILE="$PROJECT_ROOT/immich_autotag/version.py"

if [ ! -f "$LOCAL_VERSION_FILE" ]; then
  echo "[ERROR] No se encuentra $LOCAL_VERSION_FILE"
  exit 1
fi

LOCAL_VERSION=$(grep '^__version__' "$LOCAL_VERSION_FILE" | cut -d'=' -f2 | tr -d ' "')

# Si se pasa una versión como argumento, usarla. Si no, usar la de pyproject.toml
if [ "${1-}" != "" ]; then
  PKG_VERSION="$1"
else
  PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"
  if [ ! -f "$PYPROJECT_TOML" ]; then
    echo "[ERROR] No se encuentra pyproject.toml"
    exit 1
  fi
  PKG_VERSION=$(grep '^version' "$PYPROJECT_TOML" | cut -d'=' -f2 | tr -d ' "')
fi

TMPDIR="$(mktemp -d)"
cd "$TMPDIR"
pip download immich-autotag=="$PKG_VERSION" -d .
WHEEL_FILE=$(ls immich_autotag-*.whl | head -n1)
if [ ! -f "$WHEEL_FILE" ]; then
  echo "[ERROR] No se ha descargado el wheel de la versión $PKG_VERSION"
  exit 1
fi
unzip -q "$WHEEL_FILE" -d ./whl
PYPI_VERSION=$(grep '^__version__' ./whl/immich_autotag/version.py | cut -d'=' -f2 | tr -d ' "')

if [ "$LOCAL_VERSION" != "$PYPI_VERSION" ]; then
  echo "[ERROR] La versión local ($LOCAL_VERSION) y la publicada en PyPI ($PYPI_VERSION) no coinciden."
  exit 2
else
  echo "[OK] La versión local y la publicada en PyPI coinciden: $LOCAL_VERSION"
fi
