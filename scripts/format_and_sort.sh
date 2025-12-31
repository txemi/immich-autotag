#!/bin/bash
# Script para formatear y organizar imports en el proyecto, evitando .venv y librerías externas
set -x
set -e

# Directorio a formatear (por defecto, el actual)
TARGET_DIR="${1:-.}"



# Exclusiones robustas para evitar formatear .venv y otros directorios externos
BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"
ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts"


# Activa el entorno virtual del proyecto de forma robusta
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_PATH="$PROJECT_ROOT/.venv/bin/activate"
if [ ! -f "$VENV_PATH" ]; then
	echo "[ERROR] No se ha encontrado el entorno virtual en $VENV_PATH"
	echo "Ejecuta primero el script de setup: bash setup_venv.sh"
	exit 1
fi

source "$VENV_PATH"

# Instala black e isort si no están disponibles
if ! "$PROJECT_ROOT/.venv/bin/python" -c "import black" 2>/dev/null; then
	echo "Instalando black en el entorno virtual..."
	"$PROJECT_ROOT/.venv/bin/python" -m pip install black
fi
if ! "$PROJECT_ROOT/.venv/bin/python" -c "import isort" 2>/dev/null; then
	echo "Instalando isort en el entorno virtual..."
	"$PROJECT_ROOT/.venv/bin/python" -m pip install isort
fi

# Formatea el código con Black usando el Python del entorno virtual
"$PROJECT_ROOT/.venv/bin/python" -m black $BLACK_EXCLUDES "$TARGET_DIR"

# Organiza los imports con isort usando el Python del entorno virtual
"$PROJECT_ROOT/.venv/bin/python" -m isort $ISORT_SKIPS "$TARGET_DIR"
