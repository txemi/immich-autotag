#!/bin/bash
# venv_launcher.sh: Lanza un script Python usando el virtualenv del proyecto, sin importar desde dónde se invoque.
# Uso: ./venv_launcher.sh <script_python> [args...]

set -e
set -o pipefail



# Localiza la raíz del proyecto (dos niveles arriba de este script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PY="$REPO_ROOT/.venv/bin/python"

# Añade la raíz del repo al PYTHONPATH para imports absolutos
export PYTHONPATH="$REPO_ROOT"

if [ ! -x "$VENV_PY" ]; then
  echo "[FATAL] No se encontró el virtualenv en $VENV_PY" >&2
  exit 2
fi

if [ $# -lt 1 ]; then
  echo "Uso: $0 <script_python> [args...]" >&2
  exit 1
fi

PY_SCRIPT="$1"
shift

exec "$VENV_PY" "$PY_SCRIPT" "$@"
