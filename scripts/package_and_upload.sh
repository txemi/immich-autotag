#!/usr/bin/env bash
# Script para mover immich_client a la raíz, construir y subir a TestPyPI, y restaurar la carpeta
# Uso: ./scripts/package_and_upload.sh

set -euo pipefail

# Obtener el directorio donde está este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Ir al directorio raíz del proyecto (asumiendo que scripts/ está en la raíz o un subdirectorio)
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/..")"
cd "$PROJECT_ROOT"

IMMICH_CLIENT_ORIG="immich-client/immich_client"
IMMICH_CLIENT_DEST="immich_client"
IMMICH_CLIENT_BACKUP="immich-client/immich_client_backup_$(date +%s)"

# Comprobar que la carpeta existe
if [ ! -d "$IMMICH_CLIENT_ORIG" ]; then
  echo "No se encontró $IMMICH_CLIENT_ORIG. Abortando."
  exit 1
fi

# Mover la carpeta a la raíz
mv "$IMMICH_CLIENT_ORIG" "$IMMICH_CLIENT_DEST"

# Construir el paquete
python3 -m build

# Subir a TestPyPI
if ! command -v twine &> /dev/null; then
  echo "twine no está instalado. Instalando..."
  pip install --user twine
fi

twine upload --repository testpypi dist/*

# Restaurar la carpeta a su ubicación original
mv "$IMMICH_CLIENT_DEST" "$IMMICH_CLIENT_ORIG"

echo "Operación completada."
