#!/usr/bin/env bash
# Script para descargar e instalar el artefacto desde TestPyPI y probar la instalación
# Uso: ./scripts/test_install_from_testpypi.sh

set -euo pipefail

# Obtener el directorio donde está este script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Ir al directorio raíz del proyecto
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/..")"
cd "$PROJECT_ROOT"

# Comprobar que el virtual environment estándar está activo
if [ -z "${VIRTUAL_ENV:-}" ] || [ "$(basename "$VIRTUAL_ENV")" != ".venv" ]; then
  echo "[ERROR] Debes activar el entorno virtual estándar (.venv) antes de ejecutar este script."
  echo "Usa: source .venv/bin/activate"
  exit 1
fi

# Instalar el paquete desde TestPyPI (reemplaza 'immich-autotag' y versión si es necesario)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple immich-autotag

# Probar la importación del cliente generado
python -c "import immich_client; print('Importación exitosa de immich_client')"

# Probar el CLI si existe (reemplaza 'immich-autotag' por el nombre del comando si es diferente)
if command -v immich-autotag &> /dev/null; then
  echo "Probando CLI:"
  immich-autotag --help
else
  echo "No se encontró el comando CLI 'immich-autotag'."
fi

echo "Prueba de instalación completada."
