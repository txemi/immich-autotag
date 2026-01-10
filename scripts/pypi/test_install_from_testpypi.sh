#!/usr/bin/env bash
# Script para probar la instalación desde TestPyPI en un entorno limpio
# Uso: ./scripts/pypi/test_install_from_testpypi.sh

set -euo pipefail

# Detectar la raíz del repo (dos niveles arriba de este script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Extraer la versión desde pyproject.toml
PYPROJECT_TOML="$REPO_ROOT/pyproject.toml"
PKG_NAME="immich-autotag"
PKG_VERSION=$(grep '^version' "$PYPROJECT_TOML" | head -n1 | cut -d'=' -f2 | tr -d ' "')
TEMP_DIR="$REPO_ROOT/prueba_instalacion_temp"

# Crear carpeta temporal y entrar en ella
rm -rf "$TEMP_DIR"
mkdir "$TEMP_DIR"
cd "$TEMP_DIR"

# Crear y activar entorno virtual limpio
python3 -m venv venv-test
source venv-test/bin/activate

# Instalar el paquete desde TestPyPI, pero dependencias desde PyPI oficial
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  --no-cache-dir --upgrade "$PKG_NAME==$PKG_VERSION"

# Probar la importación del cliente generado
python -c "import immich_client; print('Importación exitosa de immich_client')"

# Probar el CLI si existe
if command -v "$PKG_NAME" &> /dev/null; then
  echo "Probando CLI:"
  "$PKG_NAME" --help
else
  echo "No se encontró el comando CLI '$PKG_NAME'."
fi

# Salir del entorno virtual y limpiar
deactivate
cd "$REPO_ROOT"
rm -rf "$TEMP_DIR"

echo "Prueba de instalación completada en entorno limpio."