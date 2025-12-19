#!/bin/bash
# Activa el entorno virtual y ejecuta el punto de entrada principal de la app Immich

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"

if [ ! -d "$VENV_DIR" ]; then
  echo "ERROR: No se encuentra el entorno virtual en $VENV_DIR"
  exit 1
fi

source "$VENV_DIR/bin/activate"

python "$PYTHON_SCRIPT" "$@"
