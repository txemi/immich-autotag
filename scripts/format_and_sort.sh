#!/bin/bash
# Script para formatear y organizar imports en el proyecto, evitando .venv y librerías externas

# Directorio a formatear (por defecto, el actual)
TARGET_DIR="${1:-.}"

# Excluye .venv y librerías externas
EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"


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

# Formatea el código con Black
black $EXCLUDES "$TARGET_DIR"

# Organiza los imports con isort
isort $EXCLUDES "$TARGET_DIR"
