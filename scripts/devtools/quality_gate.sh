#!/bin/bash
# ============================================================================
# Quality Gate Script: Checks and Execution Modes
# ============================================================================
# This script implements two main modes:
#   - Strict mode (default): Fails on any check error.
#   - Relaxed mode (--relaxed): Allows some non-critical checks to pass.
#
# Checks and Modes Table
# -----------------------------------------------------------------------------
# | Check                            | Description                                 | Strict   | Relaxed (CI) |
# |-----------------------------------|---------------------------------------------|----------|--------------|
# | Syntax/Indent (compileall)        | Python syntax errors                        |   ✔️     |   ✔️         |
# | ruff (lint/auto-fix)              | Linter and auto-format                      |   ✔️     |   ✔️         |
# | isort (import sorting)            | Sorts imports                               |   ✔️     |   ✔️         |
# | black (formatter)                 | Code formatter                              |   ✔️     |   ✔️         |
# | flake8 (style)                    | Style linter                                |   ✔️     |   ✔️         |
# | mypy (type check)                 | Type checking                               |   ✔️     |   Warn       |
# | uvx ssort (method order)          | Class method ordering                       |   ✔️     |   ✔️         |
# | getattr/hasattr policy            | Forbids getattr/hasattr (optional)          |   ✔️**   |   ✔️**       |
# | tuple return/type policy          | Forbids tuples as return/attribute          |   ✔️     |   ✔️         |
# | jscpd (code duplication)          | Detects code duplication                    |   ✔️     |   ✔️         |
# | Spanish character check           | Forbids Spanish text/accents                |   ✔️     |   Warn       |
# -----------------------------------------------------------------------------
# * En modo relajado, flake8 ignora E501, y flake8/mypy solo avisan, no bloquean el build.
# ** Solo si se usa --enforce-dynamic-attrs
#
# Add/modify this table if new checks are added.
# ============================================================================
##
# ------------------------------------------------------------------------------
# Prioritization table for hardening the Quality Gate (by ease of activation as blockers)
# ------------------------------------------------------------------------------
# | Priority | Check      | Reason/Estimated cost                      | Status             |
# |----------|------------|--------------------------------------------|--------------------|
# | 1        | black      | Already enforced as blocker                | ✅ Already blocker |
# | 2        | isort      | Already enforced as blocker                | ✅ Already blocker |
# | 3        | ruff       | Already enforced as blocker                | ✅ Already blocker |
# | 4        | flake8     | Medium cost, depends on rules              | ✔️ (bloquea siempre) |
# | 5        | jscpd      | Already enforced as blocker                | ✅ Already blocker |
# | 6        | uvx ssort  | Already enforced as blocker                | ✅ Already blocker |
# | 7        | mypy       | High cost, requires typing                 | Warn (relaxed)     |
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Prioritization table for robustness (static analysis checks)
# ------------------------------------------------------------------------------
# | Priority | Check  | Reason/Robustness provided                   | Status             |
# |----------|--------|----------------------------------------------|--------------------|
# | 1        | mypy   | Maximum robustness, detects real errors      | Pending            |
# | 2        | flake8 | Medium robustness, helps with style/errors   | ✔️ (bloquea siempre) |
# | 3        | ruff   | Already enforced as blocker                  | ✅ Already blocker |
# | 4        | black  | Already enforced as blocker                  | ✅ Already blocker |
# | 5        | isort  | Already enforced as blocker                  | ✅ Already blocker |
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Recommended plan to harden the Quality Gate (in order of priority):
# 1. (Done) Black is already enforced as a blocker.
# 2. (Done) Isort is already enforced as a blocker.
# 3. (Done) Ruff is already enforced as a blocker.
# 4. Activate flake8 as a blocker (medium cost, adds style/error robustness).
# 5. Activate mypy as a blocker (high cost, maximum robustness, requires typing everywhere).
#
# When the main checks table is updated, also update these tables and the plan if needed.
set -x
set -e
set -o pipefail


# Usage: ./quality_gate.sh [--check|-c] [--strict] [target_dir]
#   --strict: Enforce all checks strictly, fail on any error.
#   Default (relaxed): Ignores E501 in flake8, does not fail on uvx ssort or Spanish character check, and only warns on flake8/mypy errors.
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
	echo "Usage: $0 [--check|-c] [--strict] [target_dir]"
	echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python.";
	echo "  --strict: Enforce all checks strictly, fail on any error.";
	exit 0
fi

# Parse strict mode (default is relaxed)
RELAXED_MODE=1
for arg in "$@"; do
	if [ "$arg" = "--strict" ]; then
		RELAXED_MODE=0
	fi
done

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_NAME="immich_autotag"

# Move to repo root
cd "$REPO_ROOT"


# Only support --check and --enforce-dynamic-attrs
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

# Robust exclusions to avoid formatting .venv, jenkins_logs and other external directories
BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts --exclude jenkins_logs --line-length $MAX_LINE_LENGTH"
ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts --skip jenkins_logs --line-length $MAX_LINE_LENGTH"

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

# --- Code duplication detection with jscpd ---
echo "[CHECK] Running jscpd for code duplication detection..."
if ! command -v jscpd &> /dev/null; then
	echo "[INFO] jscpd not found, installing locally via npx..."
	JSCMD="npx jscpd"
else
	JSCMD="jscpd"
fi

# Run jscpd in check mode (non-zero exit if duplicates found)
# Use --ignore instead of --exclude for recent jscpd versions
$JSCMD --silent --min-tokens 30 --max-lines 100 --format python --ignore "**/.venv/**,**/immich-client/**,**/scripts/**" "$TARGET_DIR"
JSPCD_EXIT=$?
if [ $JSPCD_EXIT -ne 0 ]; then
	echo "[ERROR] jscpd detected code duplication. Please refactor duplicate code."
	exit 4
fi
echo "jscpd check passed: no significant code duplication detected."




# Flake8: use the same synchronized line length, print output directly, capture exit code
ensure_tool flake8 flake8
FLAKE_FAILED=0
FLAKE8_IGNORE="E203,W503"
if [ $RELAXED_MODE -eq 1 ]; then
    FLAKE8_IGNORE="$FLAKE8_IGNORE,E501"
    echo "[RELAXED MODE] E501 (line length) errors are ignored and will NOT block the build."
fi
echo "[INFO] Running flake8 (output below if any):"
"$PY_BIN" -m flake8 --max-line-length=$MAX_LINE_LENGTH --extend-ignore=$FLAKE8_IGNORE --exclude=.venv,immich-client,scripts,jenkins_logs "$TARGET_DIR"
if [ $? -ne 0 ]; then
    FLAKE_FAILED=1
fi


###############################################################
# Deterministic method ordering in Python classes              #
# ----------------------------------------------------------- #
# Historically, `uvx ssort` was used for this purpose, but:   #
#   - `uvx` has been removed from PyPI and is now a dummy.    #
#   - There is no direct alternative in PyPI or apt.          #
#   - Locally it may work if you have an old version or snap, #
#     but in CI/Jenkins and clean environments it is not viable.
# Solution:                                                   #
#   - We use `ssort` from GitHub (https://github.com/bwhmather/ssort),
#     installing it with pip directly from the repo if not present.
#   - This ensures reproducibility and that Jenkins/CI always has the tool,
#     without relying on old versions or snaps.                #
#   - If a more standard alternative appears in the future, migration will be easy.
# NOTE: Local tests may work due to previous installations,   #
# but reproducibility in CI is what matters.                  #
###############################################################


# --- Ensure ssort (bwhmather/ssort) is installed and available ---
ensure_ssort() {
	if ! command -v ssort &> /dev/null; then
		echo "[INFO] ssort not found, installing from GitHub..."
		"$PY_BIN" -m pip install git+https://github.com/bwhmather/ssort.git
	fi
}





# --- Run ssort for deterministic method ordering after syntax check ---

ensure_ssort
SSORT_FAILED=0
if [ "$CHECK_MODE" -eq 1 ]; then
	echo "[FORMAT] Running ssort in CHECK mode..."
	ssort --check "$TARGET_DIR" || SSORT_FAILED=1
else
	echo "[FORMAT] Running ssort in APPLY mode..."
	ssort "$TARGET_DIR" || SSORT_FAILED=1
fi

# Now ssort is blocking in both modes
if [ $SSORT_FAILED -ne 0 ]; then
    echo "[ERROR] ssort detected unsorted methods. Run in apply mode to fix."
    exit 1
fi



# mypy: print output directly, capture exit code
ensure_tool mypy mypy
MYPY_FAILED=0
echo "[INFO] Running mypy (output below if any):"
set +e
"$PY_BIN" -m mypy --ignore-missing-imports "$TARGET_DIR"
MYPY_EXIT_CODE=$?
set -e
if [ $MYPY_EXIT_CODE -ne 0 ]; then
    MYPY_FAILED=1
fi


# In relaxed mode, do not block on flake8/mypy errors, just warn

# --- Enhanced error reporting for flake8 and mypy ---




# --- SIMPLIFIED QUALITY GATE: LINEAR, FAIL-FAST, MODE-AWARE ---
# Flake8: always blocks (with config depending on mode)
if [ $FLAKE_FAILED -ne 0 ]; then
	echo "[ERROR] flake8 failed. See output above."
	exit 1
fi
# mypy: blocks only in strict mode
if [ $MYPY_FAILED -ne 0 ]; then
	echo "[ERROR] mypy failed. See output above."
	if [ $RELAXED_MODE -eq 1 ]; then
		echo "[RELAXED MODE] Not blocking build on mypy errors."
	else
		exit 1
	fi
fi


echo "Static checks (ruff/flake8/mypy) completed successfully."

# --- Spanish language character check (quality gate) ---
echo "Checking for Spanish language characters in source files..."
SPANISH_MATCHES=$(grep -r -n -I -E '[áéíóúÁÉÍÓÚñÑüÜ¿¡]' . --exclude-dir={.git,.venv,node_modules,dist,build,logs_local,jenkins_logs} || true)
if [ -n "$SPANISH_MATCHES" ]; then
	echo '❌ Spanish language characters detected in the following files/lines:'
	echo "$SPANISH_MATCHES"
	if [ "$RELAXED_MODE" -eq 1 ]; then
		echo '[RELAXED MODE] Not blocking build on Spanish character check.'
	else
		echo 'Build failed: Please remove all Spanish text and accents before publishing.'
		exit 1
	fi

else
	echo "✅ No Spanish language characters detected."
fi

echo "🎉 Quality Gate completed successfully!"
