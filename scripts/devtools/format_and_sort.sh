#!/bin/bash
# Script to format and organize imports in the project, avoiding .venv and external libraries
set -x
set -e

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_NAME="immich_autotag"

# Move to repo root
cd "$REPO_ROOT"

# Parse args: support optional --check (or -c) and optional target dir
CHECK_MODE=0
if [ "$1" = "--check" ] || [ "$1" = "-c" ]; then
	CHECK_MODE=1
	TARGET_DIR="${2:-$PACKAGE_NAME}"
else
	TARGET_DIR="${1:-$PACKAGE_NAME}"
fi

if [ "$CHECK_MODE" -eq 1 ]; then
	echo "[MODE] Running in CHECK mode (no files will be modified)."
else
	echo "[MODE] Running in APPLY mode (formatters may modify files)."
fi

# Robust exclusions to avoid formatting .venv and other external directories
BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts"
ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts"

# Activate project virtual environment robustly
VENV_PATH="$REPO_ROOT/.venv/bin/activate"
if [ ! -f "$VENV_PATH" ]; then
	echo "[ERROR] Virtual environment not found at $VENV_PATH"
	echo "First run the setup script: bash setup_venv.sh"
	exit 1
fi

source "$VENV_PATH"


# Chequeo de sintaxis e indentación en todos los .py del paquete
echo "Comprobando errores de sintaxis e indentación..."
echo "[CHECK] Byte-compiling Python sources in $TARGET_DIR..."
if ! "$REPO_ROOT/.venv/bin/python" -m compileall -q "$TARGET_DIR" ; then
	echo "[ERROR] Byte-compilation failed (syntax error or import-time failure). Aborting."
	exit 1
fi

# Fallback check per-file (keeps original behavior for precise messages)
find "$TARGET_DIR" -name "*.py" -exec "$REPO_ROOT/.venv/bin/python" -m py_compile {} +

# Install black and isort if not available
if ! "$REPO_ROOT/.venv/bin/python" -c "import black" 2>/dev/null; then
	echo "Installing black in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install black
fi
if ! "$REPO_ROOT/.venv/bin/python" -c "import isort" 2>/dev/null; then
	echo "Installing isort in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install isort
fi

# Organize imports with isort using the virtual environment Python
# Run isort before black, using the 'black' profile for compatibility
if [ "$CHECK_MODE" -eq 1 ]; then
	"$REPO_ROOT/.venv/bin/python" -m isort $ISORT_SKIPS --profile black --check-only "$TARGET_DIR"
else
	"$REPO_ROOT/.venv/bin/python" -m isort $ISORT_SKIPS --profile black "$TARGET_DIR"
fi

# Format code with Black using the virtual environment Python
if [ "$CHECK_MODE" -eq 1 ]; then
	"$REPO_ROOT/.venv/bin/python" -m black --check $BLACK_EXCLUDES "$TARGET_DIR"
else
	"$REPO_ROOT/.venv/bin/python" -m black $BLACK_EXCLUDES "$TARGET_DIR"
fi

echo "Formatting and import sorting completed."

# Optional static checks: flake8 (style/errors) and mypy (type checking)
echo "[CHECK] Running optional static analyzers: flake8, mypy (if available)"

# Install flake8 if not present
if ! "$REPO_ROOT/.venv/bin/python" -c "import flake8" 2>/dev/null; then
	echo "Installing flake8 in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install flake8
fi

# Run flake8 with same exclusions. Align flake8 with Black defaults
# (Black uses line-length 88 and recommends ignoring E203 and W503)
"$REPO_ROOT/.venv/bin/python" -m flake8 --max-line-length=88 \
	--extend-ignore=E203,W503 --exclude=.venv,immich-client,scripts "$TARGET_DIR" || {
	echo "[ERROR] flake8 reported issues. Fix them or run flake8 to see details.";
	exit 1;
}

# Install mypy if not present
if ! "$REPO_ROOT/.venv/bin/python" -c "import mypy" 2>/dev/null; then
	echo "Installing mypy in the virtual environment..."
	"$REPO_ROOT/.venv/bin/python" -m pip install mypy
fi

# Run mypy (ignore missing imports by default to avoid noise from external libs)
"$REPO_ROOT/.venv/bin/python" -m mypy --ignore-missing-imports "$TARGET_DIR" || {
	echo "[ERROR] mypy reported type issues. Consider fixing or adjusting mypy config.";
	exit 1;
}

echo "Static checks (flake8, mypy) completed successfully."
