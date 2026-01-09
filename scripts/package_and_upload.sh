#!/usr/bin/env bash
# Script para mover immich_client a la raíz, construir y subir a TestPyPI, y restaurar la carpeta
# Uso: ./scripts/package_and_upload.sh


set -euo pipefail
set -x
# Comprobar que el virtual environment estándar está activo
if [ -z "${VIRTUAL_ENV:-}" ] || [ "$(basename "$VIRTUAL_ENV")" != ".venv" ]; then
  echo "[ERROR] Debes activar el entorno virtual estándar (.venv) antes de ejecutar este script."
  echo "Usa: source .venv/bin/activate"
  exit 1
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

python3 -m build

# Subir a TestPyPI
if ! command -v twine &> /dev/null; then
  echo "twine no está instalado. Instalando..."
  pip install --user twine
fi

twine upload --repository testpypi dist/*


# Solo restaurar si el destino existe y el origen no
if [ -d "$IMMICH_CLIENT_DEST" ] && [ ! -d "$IMMICH_CLIENT_ORIG" ]; then
  mv "$IMMICH_CLIENT_DEST" "$IMMICH_CLIENT_ORIG"
else
  echo "No es necesario restaurar $IMMICH_CLIENT_DEST."
fi

echo "Operación completada."
