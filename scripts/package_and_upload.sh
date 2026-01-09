#!/usr/bin/env bash
# Script para mover immich_client a la raíz, construir y subir a TestPyPI, y restaurar la carpeta
# Uso: ./scripts/package_and_upload.sh

set -euo pipefail
set -x

# --- Incrementar automáticamente el número de patch en pyproject.toml ---
PYPROJECT_TOML="pyproject.toml"
if [ -f "$PYPROJECT_TOML" ]; then
  VERSION_LINE=$(grep '^version' "$PYPROJECT_TOML")
  VERSION=$(echo "$VERSION_LINE" | cut -d'=' -f2 | tr -d ' "')
  IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"
  NEW_PATCH=$((PATCH + 1))
  NEW_VERSION="$MAJOR.$MINOR.$NEW_PATCH"
  # Reemplazar la línea de versión
  sed -i "s/^version = .*/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
  echo "[INFO] Versión incrementada automáticamente: $VERSION -> $NEW_VERSION"
fi

# Comprobar y activar el virtual environment estándar si existe y no está activo
if [ -z "${VIRTUAL_ENV:-}" ] || [ "$(basename "$VIRTUAL_ENV")" != ".venv" ]; then
  if [ -d ".venv" ]; then
    echo "[INFO] Activando entorno virtual .venv..."
    # shellcheck disable=SC1091
    source .venv/bin/activate
  else
    echo "[ERROR] No se encontró el entorno virtual .venv. Por favor, créalo con 'python3 -m venv .venv' y vuelve a intentarlo."
    exit 1
  fi
fi

# Obtener el directorio donde está este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Ir al directorio raíz del proyecto (asumiendo que scripts/ está en la raíz o un subdirectorio)
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/..")"
cd "$PROJECT_ROOT"

IMMICH_CLIENT_ORIG="immich-client/immich_client"
IMMICH_CLIENT_DEST="immich_client"
IMMICH_CLIENT_BACKUP="immich-client/immich_client_backup_$(date +%s)"


# Solo mover si el destino no existe y el origen sí
if [ ! -d "$IMMICH_CLIENT_DEST" ] && [ -d "$IMMICH_CLIENT_ORIG" ]; then
  mv "$IMMICH_CLIENT_ORIG" "$IMMICH_CLIENT_DEST"
elif [ -d "$IMMICH_CLIENT_DEST" ]; then
  echo "$IMMICH_CLIENT_DEST ya está en la raíz, no se mueve."
else
  echo "No se encontró $IMMICH_CLIENT_ORIG ni $IMMICH_CLIENT_DEST. Abortando."
  exit 1
fi


# Construir el paquete
# Limpiar la carpeta dist/ antes de construir
if [ -d dist ]; then
  rm -rf dist/*
fi

# Instalar build si no está presente en el entorno virtual
if ! python3 -m build --version &> /dev/null; then
  echo "[INFO] Instalando build en el entorno virtual..."
  pip install build
fi

python3 -m build

# Subir a TestPyPI

# Instalar twine en el entorno virtual si no está presente
if ! command -v twine &> /dev/null; then
  echo "[INFO] twine no está instalado. Instalando en el entorno virtual..."
  pip install twine
fi

twine upload --verbose --repository testpypi dist/*


# Solo restaurar si el destino existe y el origen no
if [ -d "$IMMICH_CLIENT_DEST" ] && [ ! -d "$IMMICH_CLIENT_ORIG" ]; then
  mv "$IMMICH_CLIENT_DEST" "$IMMICH_CLIENT_ORIG"
else
  echo "No es necesario restaurar $IMMICH_CLIENT_DEST."
fi

echo "Operación completada."
