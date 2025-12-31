#!/bin/bash
# Script para formatear y organizar imports en el proyecto, evitando .venv y librerías externas

# Directorio a formatear (por defecto, el actual)
TARGET_DIR="${1:-.}"

# Excluye .venv y librerías externas
EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"

# Activa el entorno virtual si es necesario
# source /ruta/a/tu/entorno/.venv/bin/activate

# Formatea el código con Black
black $EXCLUDES "$TARGET_DIR"

# Organiza los imports con isort
isort $EXCLUDES "$TARGET_DIR"
