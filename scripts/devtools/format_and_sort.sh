#!/bin/bash
# Script to format and organize imports in the project, avoiding .venv and external libraries
set -x
set -e
set -o pipefail


# Usage: ./format_and_sort.sh [--check|-c] [--relaxed] [target_dir]
#   --relaxed: Ignore E501 (long lines) in flake8 and do not fail on uvx ssort errors.
#   Default (strict): All checks enforced, script fails on any error.
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
		echo "Usage: $0 [--check|-c] [--relaxed] [target_dir]"
		echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python.";
		echo "  --relaxed: Ignore E501 (long lines) in flake8 and do not fail on uvx ssort errors.";
		exit 0
fi

RELAXED_MODE=0
for arg in "$@"; do
	if [ "$arg" = "--relaxed" ]; then
		RELAXED_MODE=1
	fi
done

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_NAME="immich_autotag"

# Move to repo root
cd "$REPO_ROOT"


CHECK_MODE=0
ENFORCE_DYNAMIC_ATTRS=0
TARGET_DIR=""
for arg in "$@"; do
	if [ "$arg" = "--check" ] || [ "$arg" = "-c" ]; then
		CHECK_MODE=1
	elif [ "$arg" = "--enforce-dynamic-attrs" ]; then
		ENFORCE_DYNAMIC_ATTRS=1
	elif [[ "$arg" != --* ]]; then
		TARGET_DIR="$arg"
	fi
done
# If no positional argument was given, default to PACKAGE_NAME
if [ -z "$TARGET_DIR" ]; then
	TARGET_DIR="$PACKAGE_NAME"
fi

if [ "$CHECK_MODE" -eq 1 ]; then
	echo "[MODE] Running in CHECK mode (no files will be modified)."
else
	echo "[MODE] Running in APPLY mode (formatters may modify files)."
fi




# ---- Synchronized line length ----
# Screen line length is extracted from pyproject.toml so that all tools use the same source of truth.
extract_line_length() {
	grep -E '^[ \t]*line-length[ \t]*=' "$1" | head -n1 | sed -E 's/.*= *([0-9]+).*/\1/'
}
# IMPORTANT NOTE ABOUT max-line-length AND FLAKE8:
# ------------------------------------------------
# The line-length value is extracted from pyproject.toml and used for Black, isort, ruff, and flake8.
# However, flake8 does not read pyproject.toml by itself: if you run flake8 manually, it will use the value from .flake8.
# If you use this script, the value is passed to flake8 as an argument and everything stays in sync.
# There is only a risk of desynchronization if you edit pyproject.toml and .flake8 separately and run flake8 manually.

MAX_LINE_LENGTH=$(extract_line_length "$REPO_ROOT/pyproject.toml")
if [ -z "$MAX_LINE_LENGTH" ]; then
	echo "[WARN] Could not extract line-length from pyproject.toml, using 88 by default."
	MAX_LINE_LENGTH=88
fi

# Robust exclusions to avoid formatting .venv and other external directories
BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts --line-length $MAX_LINE_LENGTH"
ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts --line-length $MAX_LINE_LENGTH"

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


# Syntax and indentation check on all .py files in the package
echo "Checking for syntax and indentation errors..."
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

# Policy enforcement: disallow dynamic attribute access via getattr() and hasattr()
# Projects following our coding guidelines avoid these calls because they
# undermine static typing and hide missing attributes. This check is strict
# and is DISABLED by default (enabled only with --enforce-dynamic-attrs).
if [ "$ENFORCE_DYNAMIC_ATTRS" -eq 1 ]; then
	if grep -R --line-number --exclude-dir=".venv" --exclude-dir="immich-client" --exclude-dir="scripts" --include="*.py" -E "getattr\(|hasattr\(" "$TARGET_DIR"; then
		echo "[ERROR] Forbidden use of getattr(...) or hasattr(...) detected. Our style policy bans dynamic attribute access."
		echo "Fix occurrences in source (do not rely on getattr/hasattr)."
		exit 2
	fi
else
	echo "[INFO] getattr/hasattr policy enforcement is DISABLED by default. Use --enforce-dynamic-attrs to enable."
fi

# Policy enforcement: disallow returning tuple literals or annotated Tuple types
echo "[CHECK] Disallow tuple returns and tuple-typed class members (project policy)"
"$PY_BIN" "${REPO_ROOT}/scripts/devtools/check_no_tuples.py" "$TARGET_DIR" --exclude ".venv,immich-client,scripts" || {
    echo "[ERROR] Tuple usage policy violations detected. Replace tuples with typed classes/dataclasses.";
    exit 3;
}



# Flake8: use the same synchronized line length

ensure_tool flake8 flake8
FLAKE_FAILED=0
FLAKE8_IGNORE="E203,W503"
if [ $RELAXED_MODE -eq 1 ]; then
	FLAKE8_IGNORE="$FLAKE8_IGNORE,E501"
fi
"$PY_BIN" -m flake8 --max-line-length=$MAX_LINE_LENGTH --extend-ignore=$FLAKE8_IGNORE --exclude=.venv,immich-client,scripts "$TARGET_DIR" || FLAKE_FAILED=1


# --- Ensure uvx is installed and run ssort for deterministic method ordering ---
ensure_uvx() {
	if ! command -v uvx &> /dev/null; then
		echo "[INFO] uvx not found, installing via pip..."
		"$PY_BIN" -m pip install uvx-tool
	fi
}



# --- Run uvx ssort for deterministic method ordering after syntax check ---

ensure_uvx
UVX_FAILED=0
if [ "$CHECK_MODE" -eq 1 ]; then
		echo "[FORMAT] Running uvx ssort in CHECK mode..."
		uvx ssort --check "$TARGET_DIR" || UVX_FAILED=1
else
		echo "[FORMAT] Running uvx ssort in APPLY mode..."
		uvx ssort "$TARGET_DIR" || UVX_FAILED=1
fi

# In relaxed mode, do not fail on uvx ssort errors
if [ $UVX_FAILED -ne 0 ]; then
	if [ $RELAXED_MODE -eq 1 ]; then
		echo "[WARNING] uvx ssort failed, but continuing due to relaxed mode."
		UVX_FAILED=0
	else
		echo "[ERROR] uvx ssort detected unsorted methods. Run in apply mode to fix."
		exit 1
	fi
fi

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
