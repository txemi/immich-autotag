#!/bin/bash
# Script para formatear y organizar imports en el proyecto, evitando .venv y librerías externas

# Directorio a formatear (por defecto, el actual)
TARGET_DIR="${1:-.}"

# Excluye .venv y librerías externas
EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"


# Activa el entorno virtual del proyecto de forma robusta
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
PROJECT_ROOT="$SCRIPT_DIR/.."
source "$PROJECT_ROOT/.venv/bin/activate"

# Formatea el código con Black
black $EXCLUDES "$TARGET_DIR"

# Organiza los imports con isort
isort $EXCLUDES "$TARGET_DIR"
