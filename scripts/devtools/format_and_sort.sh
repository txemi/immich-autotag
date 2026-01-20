#!/bin/bash
# Script to format and organize imports in the project, avoiding .venv and external libraries
set -x
set -e
set -o pipefail

# Usage: ./format_and_sort.sh [--check|-c] [target_dir]
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo "Usage: $0 [--check|-c] [target_dir]"
	echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python.";
	exit 0
fi

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
VENV_ACTIVATE="$REPO_ROOT/.venv/bin/activate"
PY_BIN=""
if [ -f "$VENV_ACTIVATE" ]; then
	# Use project venv when available
	source "$VENV_ACTIVATE"
	PY_BIN="$REPO_ROOT/.venv/bin/python"
else
	echo "[WARN] .venv not found at $REPO_ROOT/.venv — falling back to system python (this may install tools globally)."
	PY_BIN="$(command -v python3 || command -v python)"
	if [ -z "$PY_BIN" ]; then
		echo "[ERROR] No python executable found. Create a virtualenv at .venv or install python3.";
		exit 1
	fi
fi


# Chequeo de sintaxis e indentación en todos los .py del paquete
echo "Comprobando errores de sintaxis e indentación..."
echo "[CHECK] Byte-compiling Python sources in $TARGET_DIR..."
if ! "$PY_BIN" -m compileall -q "$TARGET_DIR" ; then
	echo "[ERROR] Byte-compilation failed (syntax error or import-time failure). Aborting."
	exit 1
fi

# Fallback check per-file (keeps original behavior for precise messages)
find "$TARGET_DIR" -name "*.py" -exec "$PY_BIN" -m py_compile {} +

# Install black and isort if not available
# Ensure development tooling is available (install into venv if present, otherwise warn)
ensure_tool() {
	tool_import_check="$1"
	tool_pkg="$2"
	if ! "$PY_BIN" -c "import ${tool_import_check}" 2>/dev/null; then
		echo "Installing ${tool_pkg} into environment ($PY_BIN)..."
		"$PY_BIN" -m pip install "${tool_pkg}"
	fi
}

ensure_tool ruff ruff
ensure_tool black black
ensure_tool isort isort

# Run ruff first (auto-fix/format where possible)
RUF_FAILED=0
if [ "$CHECK_MODE" -eq 1 ]; then
	"$PY_BIN" -m ruff check --fix "$TARGET_DIR" || RUF_FAILED=1
else
	"$PY_BIN" -m ruff check --fix "$TARGET_DIR" || RUF_FAILED=1
fi

# Organize imports with isort using the environment Python (isort before black)
ISORT_FAILED=0
if [ "$CHECK_MODE" -eq 1 ]; then
	"$PY_BIN" -m isort $ISORT_SKIPS --profile black --check-only "$TARGET_DIR" || ISORT_FAILED=1
else
	"$PY_BIN" -m isort $ISORT_SKIPS --profile black "$TARGET_DIR" || ISORT_FAILED=1
fi

# Format code with Black using the environment Python
BLACK_FAILED=0
if [ "$CHECK_MODE" -eq 1 ]; then
	"$PY_BIN" -m black --check $BLACK_EXCLUDES "$TARGET_DIR" || BLACK_FAILED=1
else
	"$PY_BIN" -m black $BLACK_EXCLUDES "$TARGET_DIR" || BLACK_FAILED=1
fi

TOOL_FAILURES=0
if [ $RUF_FAILED -ne 0 ]; then TOOL_FAILURES=$((TOOL_FAILURES+1)); fi
if [ $ISORT_FAILED -ne 0 ]; then TOOL_FAILURES=$((TOOL_FAILURES+1)); fi
if [ $BLACK_FAILED -ne 0 ]; then TOOL_FAILURES=$((TOOL_FAILURES+1)); fi

if [ $TOOL_FAILURES -ne 0 ]; then
	echo "[WARNING] One or more formatting tools reported issues. Details:"
	[ $RUF_FAILED -ne 0 ] && echo " - ruff reported/fixed issues (exit code $RUF_FAILED)."
	[ $ISORT_FAILED -ne 0 ] && echo " - isort reported issues (exit code $ISORT_FAILED)."
	[ $BLACK_FAILED -ne 0 ] && echo " - black reported issues (exit code $BLACK_FAILED)."
	if [ "$CHECK_MODE" -eq 1 ]; then
		echo "Run in apply mode to let the script attempt to fix formatting problems or run the commands locally to inspect diffs."
	fi
fi

echo "Formatting and import sorting completed."

# Optional static checks: flake8 (style/errors) and mypy (type checking)
echo "[CHECK] Running optional static analyzers: flake8, mypy (if available)"

ensure_tool flake8 flake8
FLAKE_FAILED=0
"$PY_BIN" -m flake8 --max-line-length=88 --extend-ignore=E203,W503 --exclude=.venv,immich-client,scripts "$TARGET_DIR" || FLAKE_FAILED=1

ensure_tool mypy mypy
MYPY_FAILED=0
"$PY_BIN" -m mypy --ignore-missing-imports "$TARGET_DIR" || MYPY_FAILED=1

if [ $FLAKE_FAILED -ne 0 ] || [ $MYPY_FAILED -ne 0 ]; then
	echo "[WARNING] Static analyzers reported issues:"
	[ $FLAKE_FAILED -ne 0 ] && echo " - flake8 failed (exit code $FLAKE_FAILED)"
	[ $MYPY_FAILED -ne 0 ] && echo " - mypy failed (exit code $MYPY_FAILED)"
	exit 1
fi

echo "Static checks (ruff/flake8/mypy) completed successfully."
