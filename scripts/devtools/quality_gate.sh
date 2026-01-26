#!/bin/bash

# ============================================================================
# QUALITY GATE SCRIPT: CHECKS AND EXECUTION MODES
# ============================================================================
#
# Usage:
#   ./quality_gate.sh [--check|-c] [--strict] [--target] [--relaxed] [target_dir]
#
# Modes:
#   --strict
#     - Applies ALL checks strictly.
#     - Any error or warning in any check BLOCKS the build.
#     - No error is ignored (format, style, types, duplication, architecture, etc).
#     - Not recommended for CI/pipelines unless code is perfect.
#
#   --relaxed
#     - Applies all checks, but some only warn and DO NOT block the build.
#     - Checks that DO NOT block in relaxed mode:
#         * flake8: E501 (long lines) ignored, other errors may block.
#         * ruff: E501 ignored.
#         * mypy: only warns, does not block.
#         * Spanish characters: only warns, does not block.
#     - The rest of checks CAN block the build if they fail:
#         * Python syntax errors
#         * Code duplication (jscpd)
#         * Architecture contracts (import-linter)
#         * Forbidden tuples
#         * getattr/hasattr (only if --enforce-dynamic-attrs)
#         * Method order (ssort)
#         * Bash formatting (shfmt)
#         * isort, black, ruff (except E501)
#
#   --target
#     - Intermediate mode for Quality Gate improvement branches.
#     - Blocks the build ONLY for a selected subset of warnings/errors (currently: mypy arg-type, call-arg, return-value).
#     - The rest behave as in relaxed mode (warn only).
#     - Use this mode to progressively raise the bar in dedicated branches.
#
#   --check   Only check, do not modify files (default is apply/fix mode).
#   --enforce-dynamic-attrs  Enforce ban on getattr/hasattr (advanced).
#
# If no [target_dir] is given, defaults to the main package.
#
# =====================
# Quality Gate Checks Table (reference)
# =====================
# | Check                            | Description                                 | Strict   | Relaxed (CI) | Target (improvement) |
# |-----------------------------------|---------------------------------------------|----------|--------------|---------------------|
# | Syntax/Indent (compileall)        | Python syntax errors                        |   ✔️     |   ✔️         |   ✔️                |
# | ruff (lint/auto-fix)              | Linter and auto-format                      |   ✔️     |   ✔️         |   ✔️                |
# | isort (import sorting)            | Sorts imports                               |   ✔️     |   ✔️         |   ✔️                |
# | black (formatter)                 | Code formatter                              |   ✔️     |   ✔️         |   ✔️                |
# | flake8 (style)                    | Style linter                                |   ✔️     |   ✔️         |   ✔️                |
# | flake8 (E501 long lines)          | Line length                                 |   ✔️     |   Ignored    |   Ignored           |
# | ruff (E501 long lines)            | Line length                                 |   ✔️     |   Ignored    |   Ignored           |
# | mypy (type check)                 | Type checking                               |   ✔️     |   Warn only  |   Warn only         |
# | mypy (arg-type/call-arg/return-value) | Type errors (subset)                   |   ✔️     |   Warn only  |   ✔️                |
# | uvx ssort (method order)          | Class method ordering                       |   ✔️**   |   ✔️**       |   ✔️**              |
# | tuple return/type policy          | Forbids tuples as return/attribute          |   ✔️     |   ✔️         |   ✔️                |
# | jscpd (code duplication)          | Detects code duplication                    |   ✔️     |   ✔️         |   ✔️                |
# | Spanish character check           | Forbids Spanish text/accents                |   ✔️     |   Warn       |   Warn              |
# -----------------------------------------------------------------------------
# * In relaxed mode, flake8/ruff ignore E501, and mypy only warns, does not block the build.
# ** Only if --enforce-dynamic-attrs is used
#
# =====================
# Quality Gate Objectives Table (current/future)
# =====================
# | Objective (subset/block)          | Status      | Plan/Notes                       |
# |-----------------------------------|-------------|----------------------------------|
# | mypy arg-type/call-arg/return-value | In progress | Target mode blocks these errors  |
# | mypy attr-defined                 | Future      | Warn only, will block in future  |
# | Spanish character check           | Future      | Warn only, will block in future  |
# | flake8/ruff E501                  | Future      | Ignored, will block in future    |
#

set -x
set -e
set -o pipefail
# Trap for unexpected errors to always print a clear message before exit
trap 'if [ $? -ne 0 ]; then echo "[FATAL] Quality Gate aborted unexpectedly. Check the output above for details."; fi' EXIT

SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PACKAGE_NAME="immich_autotag"
cd "$REPO_ROOT"

###############################################################################
# Function: parse_args_and_globals
# Description: Parses command-line arguments and defines global variables.
# Globals set: QUALITY_LEVEL, CHECK_MODE, ENFORCE_DYNAMIC_ATTRS, TARGET_DIR
# Usage: parse_args_and_globals "$@"
# Returns: Exports global variables and may terminate the script in help mode
###############################################################################
parse_args_and_globals() {
	if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
		echo "Usage: $0 [--check|-c] [--strict] [target_dir]"
		echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python."
		echo "  --strict: Enforce all checks strictly, fail on any error."
		exit 0
	fi

	# Local variables for parsing
	local arg

	CHECK_MODE="APPLY" # Possible values: APPLY, CHECK
	QUALITY_LEVEL=""   # Possible values: STRICT, RELAXED
	ENFORCE_DYNAMIC_ATTRS=0
	TARGET_DIR=""
	for arg in "$@"; do
		if [ "$arg" = "--strict" ]; then
			QUALITY_LEVEL="STRICT"
		elif [ "$arg" = "--relaxed" ]; then
			QUALITY_LEVEL="RELAXED"
		elif [ "$arg" = "--target" ]; then
			QUALITY_LEVEL="TARGET"
		elif [ "$arg" = "--check" ] || [ "$arg" = "-c" ]; then
			CHECK_MODE="CHECK"
		elif [ "$arg" = "--apply" ]; then
			CHECK_MODE="APPLY"
		elif [ "$arg" = "--enforce-dynamic-attrs" ]; then
			ENFORCE_DYNAMIC_ATTRS=1
		elif [[ "$arg" != --* ]]; then
			TARGET_DIR="$arg"
		fi
	done
	# Si el usuario no fuerza QUALITY_LEVEL, por defecto RELAXED
	if [ -z "$QUALITY_LEVEL" ]; then
		QUALITY_LEVEL="RELAXED"
	fi
	# If no positional argument was given, default to PACKAGE_NAME
	if [ -z "$TARGET_DIR" ]; then
		TARGET_DIR="$PACKAGE_NAME"
	fi

	export QUALITY_LEVEL CHECK_MODE ENFORCE_DYNAMIC_ATTRS TARGET_DIR

	if [ "$QUALITY_LEVEL" = "STRICT" ]; then
		echo "[QUALITY_LEVEL] Running in STRICT mode (all checks enforced, fail on any error)."
	elif [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		echo "[QUALITY_LEVEL] Running in RELAXED mode (some checks are warnings only)."
	elif [ "$QUALITY_LEVEL" = "TARGET" ]; then
		echo "[QUALITY_LEVEL] Running in TARGET mode (selected errors block, rest warn only)."
	fi

	if [ "$CHECK_MODE" = "CHECK" ]; then
		echo "[CHECK_MODE] Running in CHECK mode (no files will be modified)."
	elif [ "$CHECK_MODE" = "APPLY" ]; then
		echo "[CHECK_MODE] Running in APPLY mode (formatters may modify files)."
	fi
}

###############################################################################
# Function: check_shfmt
# Description: Checks and formats Bash scripts using shfmt.
# Globals: CHECK_MODE
# Returns: 0 if passes, 1 if formatting errors or shfmt missing
###############################################################################
check_shfmt() {
	echo ""
	echo "==============================="
	echo "SECTION 1: BASH SCRIPT FORMATTING CHECK (shfmt)"
	echo "==============================="
	echo ""

	local bash_scripts
	# Require shfmt to be installed
	if ! command -v shfmt >/dev/null 2>&1; then
		echo "[ERROR] shfmt is not installed. Please install it to pass the quality gate."
		echo "You can install it with: sudo apt-get install shfmt  # or equivalent for your system"
		return 1
	fi

	# Find relevant bash scripts (adjust pattern if needed)
	bash_scripts=$(find scripts -type f -name "*.sh")

	# Run shfmt according to mode
	if [ "$CHECK_MODE" = "CHECK" ]; then
		if ! shfmt -d $bash_scripts; then
			echo "[ERROR] There are formatting issues in Bash scripts. Run 'shfmt -w scripts/' to fix them."
			return 1
		fi
	else
		echo "[INFO] Applying automatic formatting to Bash scripts with shfmt..."
		shfmt -w $bash_scripts
	fi
	return 0
}

###############################################################################
# Function: setup_max_line_length
# Description: Extracts the line-length value from pyproject.toml and exports it as MAX_LINE_LENGTH.
# Globals set: MAX_LINE_LENGTH
###############################################################################
setup_max_line_length() {
	local extract_line_length
	extract_line_length() {
		grep -E '^[ \t]*line-length[ \t]*=' "$1" | head -n1 | sed -E 's/.*= *([0-9]+).*/\1/'
	}
	local max_line_length_local
	max_line_length_local=$(extract_line_length "$REPO_ROOT/pyproject.toml")
	if [ -z "$max_line_length_local" ]; then
		echo "[WARN] Could not extract line-length from pyproject.toml, using 88 by default."
		max_line_length_local=88
	fi
	export MAX_LINE_LENGTH="$max_line_length_local"
}

###############################################################################
# Function: setup_python_env
# Description: Activates the project virtual environment or uses system Python.
# Globals set: PY_BIN
# Returns: nothing, but exports PY_BIN or exits if no Python is available
###############################################################################
setup_python_env() {
	VENV_ACTIVATE="$REPO_ROOT/.venv/bin/activate"
	echo "[INFO] Ejecutando setup_venv.sh --dev para asegurar el entorno y dependencias..."
	if [ -f "$REPO_ROOT/setup_venv.sh" ]; then
		chmod +x "$REPO_ROOT/setup_venv.sh"
		bash "$REPO_ROOT/setup_venv.sh" --dev
	else
		echo "[ERROR] setup_venv.sh not found at $REPO_ROOT. Cannot set up development environment."
		exit 1
	fi
	if [ -f "$VENV_ACTIVATE" ]; then
		# Use project venv when available
		source "$VENV_ACTIVATE"
		PY_BIN="$REPO_ROOT/.venv/bin/python"
	else
		echo "[WARN] .venv not found at $REPO_ROOT/.venv — falling back to system python (this may install tools globally)."
		PY_BIN="$(command -v python3 || command -v python)"
		if [ -z "$PY_BIN" ]; then
			echo "[ERROR] No python executable found. Create a virtualenv at .venv or install python3."
			exit 1
		fi
	fi
	export PY_BIN
}

###############################################################################
# Function: check_python_syntax
# Description: Compiles Python files to detect syntax errors.
# Globals: PY_BIN, TARGET_DIR
# Returns: 0 if passes, 1 if syntax errors
###############################################################################
check_python_syntax() {
	local result
	echo "Checking for syntax and indentation errors..."
	echo "[CHECK] Byte-compiling Python sources in $TARGET_DIR..."
	if ! "$PY_BIN" -m compileall -q "$TARGET_DIR"; then
		echo "[ERROR] Byte-compilation failed (syntax error or import-time failure). Aborting."
		return 1
	fi
	# Fallback check per-file (keeps original behavior for precise messages)
	find "$TARGET_DIR" -name "*.py" -exec "$PY_BIN" -m py_compile {} +
	return 0
}

# Call the second check

###############################################################################
# Function: ensure_tool
# Description: Installs a Python tool in the current environment if missing.
# Globals: PY_BIN
# Usage: ensure_tool <import_name> <package_name>
# Returns: nothing, but installs the package if needed
###############################################################################
ensure_tool() {
	local tool_import_check="$1"
	local tool_pkg="$2"
	if ! "$PY_BIN" -c "import ${tool_import_check}" 2>/dev/null; then
		echo "Installing ${tool_pkg} into environment ($PY_BIN)..."
		"$PY_BIN" -m pip install "${tool_pkg}"
	fi
}

###############################################################################
# Function: check_isort
# Description: Sorts Python imports using isort.
# Globals: CHECK_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 if passes, 1 if sorting issues
###############################################################################
check_isort() {
	local isort_skips isort_exit
	ensure_tool isort isort
	isort_skips="--skip .venv --skip immich-client --skip scripts --skip jenkins_logs --line-length $MAX_LINE_LENGTH"
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m isort $isort_skips --profile black --check-only "$TARGET_DIR"
		isort_exit=$?
	else
		"$PY_BIN" -m isort $isort_skips --profile black "$TARGET_DIR"
		isort_exit=$?
	fi
	if [ $isort_exit -ne 0 ]; then
		echo "[WARNING] isort reported issues."
		if [ "$CHECK_MODE" -eq 1 ]; then
			echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
			return 1
		fi
	fi
	return 0
}

###############################################################################
# SECTION 9B: SSORT (DETERMINISTIC METHOD ORDERING)
# -----------------------------------------------------------------------------
# - ssort: Ensures deterministic method ordering in Python classes.
# -----------------------------------------------------------------------------
# Deterministic method ordering in Python classes
# -----------------------------------------------------------
# Historically, `uvx ssort` was used for this purpose, but:
#   - `uvx` has been removed from PyPI and is now a dummy.
#   - There is no direct alternative in PyPI or apt.
#   - Locally it may work if you have an old version or snap,
#     but in CI/Jenkins and clean environments it is not viable.
# Solution:
#   - We use `ssort` from GitHub (https://github.com/bwhmather/ssort),
#     installing it with pip directly from the repo if not present.
#   - This ensures reproducibility and that Jenkins/CI always has the tool,
#     without relying on old versions or snaps.
#   - If a more standard alternative appears in the future, migration will be easy.
# NOTE: Local tests may work due to previous installations,
# but reproducibility in CI is what matters.
###############################################################################

###############################################################################
# Function: ensure_ssort
# Description: Installs ssort from GitHub if not available in the environment.
# Globals: PY_BIN
# Returns: nothing, but installs ssort if needed
###############################################################################
ensure_ssort() {
	if ! command -v ssort &>/dev/null; then
		echo "[INFO] ssort not found, installing from GitHub..."
		"$PY_BIN" -m pip install git+https://github.com/bwhmather/ssort.git
	fi
}

###############################################################################
# Function: check_ssort
# Description: Sorts Python class methods deterministically using ssort.
# Globals: CHECK_MODE, TARGET_DIR
# Returns: 0 if passes, 1 if unsorted methods
###############################################################################
check_ssort() {
	local ssort_failed=0
	ensure_ssort
	if [ "$CHECK_MODE" -eq 1 ]; then
		echo "[FORMAT] Running ssort in CHECK mode..."
		ssort --check "$TARGET_DIR" || ssort_failed=1
	else
		echo "[FORMAT] Running ssort in APPLY mode..."
		ssort "$TARGET_DIR" || ssort_failed=1
	fi
	if [ $ssort_failed -ne 0 ]; then
		echo "[ERROR] ssort detected unsorted methods. Run in apply mode to fix."
		echo "[EXIT] Quality Gate failed due to ssort ordering errors."
		return 1
	fi
	return 0
}

###############################################################################
# Function: check_ruff
# Description: Lint and auto-fix Python style using ruff.
# Globals: CHECK_MODE, RELAXED_MODE, PY_BIN, TARGET_DIR
# Returns: 0 if passes, 1 if style issues
###############################################################################
check_ruff() {
	local ruff_ignore="" ruff_exit
	ensure_tool ruff ruff
	if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		ruff_ignore="--ignore E501"
		echo "[RELAXED MODE] Ruff will ignore E501 (line length) and will NOT block the build for it."
	fi
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m ruff check --fix $ruff_ignore "$TARGET_DIR"
		ruff_exit=$?
	else
		"$PY_BIN" -m ruff check --fix $ruff_ignore "$TARGET_DIR"
		ruff_exit=$?
	fi
	if [ $ruff_exit -ne 0 ]; then
		echo "[WARNING] ruff reported/fixed issues."
		if [ "$CHECK_MODE" -eq 1 ]; then
			echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
			return 1
		fi
	fi
	return 0
}

###############################################################################
# Function: check_black
# Description: Formats Python code using Black.
# Globals: CHECK_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 if passes, 1 if formatting issues
###############################################################################
check_black() {
	local black_excludes black_exit
	# Format code with Black using the environment Python
	ensure_tool black black
	black_excludes="--exclude .venv --exclude immich-client --exclude scripts --exclude jenkins_logs --line-length $MAX_LINE_LENGTH"
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m black --check $black_excludes "$TARGET_DIR"
		black_exit=$?
	else
		"$PY_BIN" -m black $black_excludes "$TARGET_DIR"
		black_exit=$?
	fi
	if [ $black_exit -ne 0 ]; then
		echo "[WARNING] black reported issues."
		if [ "$CHECK_MODE" = "CHECK" ]; then
			echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
			return 1
		fi
	fi
	return 0
}

###############################################################################
# Function: check_no_dynamic_attrs
# Description: Forbids the use of getattr/hasattr for static typing safety.
# Globals: ENFORCE_DYNAMIC_ATTRS, TARGET_DIR
# Returns: 0 if passes, 1 if forbidden uses detected
###############################################################################
check_no_dynamic_attrs() {
	local matches
	# Policy enforcement: disallow dynamic attribute access via getattr() and hasattr()
	# Projects following our coding guidelines avoid these calls because they
	# undermine static typing and hide missing attributes. This check is strict
	# and is DISABLED by default (enabled only with --enforce-dynamic-attrs).
	if [ "$ENFORCE_DYNAMIC_ATTRS" -eq 1 ]; then
		matches=$(grep -R --line-number --exclude-dir=".venv" --exclude-dir="immich-client" --exclude-dir="scripts" --include="*.py" -E "getattr\(|hasattr\(" "$TARGET_DIR" || true)
		if [ -n "$matches" ]; then
			echo "$matches"
			echo "[ERROR] Forbidden use of getattr(...) or hasattr(...) detected. Our style policy bans dynamic attribute access."
			echo "Fix occurrences in source (do not rely on getattr/hasattr)."
			return 1
		fi
	else
		echo "[INFO] getattr/hasattr policy enforcement is DISABLED by default. Use --enforce-dynamic-attrs to enable."
	fi
	return 0
}

###############################################################################
# Function: check_no_tuples
# Description: Forbids the use of tuples as return values or class attributes.
# Globals: PY_BIN, REPO_ROOT, TARGET_DIR
# Returns: 0 if passes, 1 if forbidden tuples detected
###############################################################################
check_no_tuples() {
	local result
	echo "[CHECK] Disallow tuple returns and tuple-typed class members (project policy)"
	"$PY_BIN" "${REPO_ROOT}/scripts/devtools/check_no_tuples.py" "$TARGET_DIR" --exclude ".venv,immich-client,scripts" || {
		echo "[ERROR] Tuple usage policy violations detected. Replace tuples with typed classes/dataclasses."
		return 1
	}
	return 0
}

###############################################################################
# Function: check_jscpd
# Description: Detects code duplication using jscpd.
# Globals: TARGET_DIR
# Returns: 0 if passes, 1 if duplication found
###############################################################################
check_jscpd() {
	local jscmd jscpd_exit
	echo "[CHECK] Running jscpd for code duplication detection..."
	if ! command -v jscpd &>/dev/null; then
		echo "[INFO] jscpd not found, installing locally via npx..."
		jscmd="npx jscpd"
	else
		jscmd="jscpd"
	fi
	# Run jscpd in check mode (non-zero exit if duplicates found)
	# Use --ignore instead of --exclude for recent jscpd versions
	$jscmd --silent --min-tokens 30 --max-lines 100 --format python --ignore "**/.venv/**,**/immich-client/**,**/scripts/**" "$TARGET_DIR"
	jscpd_exit=$?
	if [ $jscpd_exit -ne 0 ]; then
		echo "[ERROR] jscpd detected code duplication. Please refactor duplicate code."
		return 1
	fi
	echo "jscpd check passed: no significant code duplication detected."
	return 0
}

###############################################################################
# Function: check_flake8
# Description: Lint for Python style and errors using flake8.
# Globals: RELAXED_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 if passes, 1 if style errors
###############################################################################
check_flake8() {
	local flake_failed=0 flake8_ignore
	ensure_tool flake8 flake8
	flake8_ignore="E203,W503"
	if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		flake8_ignore="$flake8_ignore,E501"
		echo "[RELAXED MODE] E501 (line length) errors are ignored and will NOT block the build."
	fi
	echo "[INFO] Running flake8 (output below if any):"
	"$PY_BIN" -m flake8 --max-line-length=$MAX_LINE_LENGTH --extend-ignore=$flake8_ignore --exclude=.venv,immich-client,scripts,jenkins_logs "$TARGET_DIR"
	if [ $? -ne 0 ]; then
		flake_failed=1
	fi
	if [ $flake_failed -ne 0 ]; then
		if [ "$QUALITY_LEVEL" = "RELAXED" ] || [ "$QUALITY_LEVEL" = "TARGET" ]; then
			echo "[WARNING] flake8 failed, but relaxed/target mode is enabled. See output above."
			echo "[RELAXED/TARGET MODE] Not blocking build on flake8 errors."
		else
			echo "[ERROR] flake8 failed. See output above."
			return 1
		fi
	fi
	return 0
}

###############################################################################
# Function: check_mypy
# Description: Static type checking using mypy.
# Globals: PY_BIN, TARGET_DIR
# Returns: 0 if passes, 1 if type errors
###############################################################################
check_mypy() {
	local mypy_failed=0 mypy_output mypy_exit_code mypy_error_count mypy_files_count
	ensure_tool mypy mypy
	echo "[INFO] Running mypy (output below if any):"
	set +e
	mypy_output=$($PY_BIN -m mypy --ignore-missing-imports "$TARGET_DIR" 2>&1)
	mypy_exit_code=$?
	set -e
	if [ $mypy_exit_code -ne 0 ]; then
		mypy_failed=1
	fi
	if [ $mypy_failed -ne 0 ]; then
		echo "$mypy_output"
		# Count errors: lines containing 'error:'
		mypy_error_count=$(echo "$mypy_output" | grep -c 'error:')
		mypy_files_count=$(echo "$mypy_output" | grep -o '^[^:]*:' | cut -d: -f1 | sort | uniq | wc -l)
		echo "[ERROR] MYPY FAILED. TOTAL ERRORS: $mypy_error_count IN $mypy_files_count FILES."
		echo "[INFO] Command executed: $PY_BIN -m mypy --ignore-missing-imports $TARGET_DIR"
		if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
			echo '[WARNING] mypy failed, but relaxed mode is enabled. See output above.'
			echo '[RELAXED MODE] Not blocking build on mypy errors.'
		elif [ "$QUALITY_LEVEL" = "TARGET" ]; then
			# Only block for arg-type, call-arg, return-value errors
			mypy_block_count=$(echo "$mypy_output" | grep -E '\[(arg-type|call-arg|return-value)\]' | wc -l)
			if [ "$mypy_block_count" -gt 0 ]; then
				echo "\n\n❌❌❌ QUALITY GATE BLOCKED ❌❌❌"
				echo "🚨 MYPY: $mypy_block_count CRITICAL ERRORS (ARG-TYPE, CALL-ARG, RETURN-VALUE) DETECTED 🚨"
				echo "[EXIT] QUALITY GATE FAILED DUE TO CRITICAL MYPY ERRORS."
				return 1
			else
				echo '[TARGET MODE] Only non-critical mypy errors found. Not blocking build.'
			fi
		else
			echo '[EXIT] Quality Gate failed due to mypy errors.'
			return 1
		fi
	fi
	echo "Static checks (ruff/flake8/mypy) completed successfully."
	return 0
}

###############################################################################
# Function: check_no_spanish_chars
# Description: Forbids Spanish/accented characters in source code.
# Globals: RELAXED_MODE
# Returns: 0 if passes, 1 if forbidden characters detected
###############################################################################
check_no_spanish_chars() {
	local spanish_matches
	echo "Checking for Spanish language characters in source files..."

	# Spanish word list
	local SPANISH_WORDS='si
solo
mantenemos
compatibilidad
devolviendo
lista
soporta
estructura
cambiado
tenemos
usamos
comentario
ejemplo
devuelve
menos
muy
aquellos
aquellas
siempre
nunca
antes
hoy
mañana
ayer
entonces
luego
mientras
durante
nuevo
nueva
nuevos
nuevas
viejo
vieja
viejos
viejas
primero
primera
primeros
primeras
mejor
peor
mayor
menor
grande
importante
interesante
lento
posible
imposible
correcto
incorrecto
verdadero
falso
cierto
seguro
probable
improbable
claro
oscuro
complicado
complejo
sencillo'
	local SPANISH_WORD_PATTERN
	SPANISH_WORD_PATTERN=$(echo "$SPANISH_WORDS" | paste -sd '|' -)
	local SPANISH_PATTERN="[áéíóúÁÉÍÓÚñÑüÜ¿¡]|\\b(${SPANISH_WORD_PATTERN})\\b"

	# Get relative paths for exclusion
	local SCRIPT_ABS_PATH QUALITY_GATE_ABS_PATH SCRIPT_REL_PATH QUALITY_GATE_REL_PATH
	SCRIPT_ABS_PATH="$(realpath "$0")"
	QUALITY_GATE_ABS_PATH="$(realpath "$BASH_SOURCE")"
	SCRIPT_REL_PATH="${SCRIPT_ABS_PATH#$PWD/}"
	QUALITY_GATE_REL_PATH="${QUALITY_GATE_ABS_PATH#$PWD/}"

	# Get git-tracked files and exclude this script and quality_gate.sh
	local files_to_check
	files_to_check=$(git ls-files | grep -v "$SCRIPT_REL_PATH" | grep -v "$QUALITY_GATE_REL_PATH")

	# Search for Spanish characters/words in the selected files
	spanish_matches=$(echo "$files_to_check" | xargs grep -n -I -E "$SPANISH_PATTERN" || true)

	if [ -n "$spanish_matches" ]; then
		echo '❌ Spanish language characters detected in the following files/lines:'
		echo "$spanish_matches"
		# Count matches and affected files
		local match_count file_count
		match_count=$(echo "$spanish_matches" | grep -c '^')
		file_count=$(echo "$spanish_matches" | cut -d: -f1 | sort | uniq | wc -l)
		echo "Total matches: $match_count | Files affected: $file_count"
		echo '[EXIT] Quality Gate failed due to forbidden Spanish characters.'
		echo 'Build failed: Please remove all Spanish text and accents before publishing.'
		return 1
	else
		echo "✅ No Spanish language characters detected."
	fi
	return 0
}

###############################################################################
# Function: check_import_linter
# Description: Verifies architectural import contracts using import-linter (lint-imports)
# Globals: REPO_ROOT
# Returns: 0 if passes, 1 if contracts are broken
###############################################################################
check_import_linter() {
	echo "[CHECK] Running import-linter (lint-imports) for architectural contracts..."
	if ! command -v lint-imports >/dev/null 2>&1; then
		echo "[ERROR] lint-imports (import-linter) is not installed or not in PATH."
		echo "Install it with: pip install import-linter"
		return 1
	fi
	if ! lint-imports --config "$REPO_ROOT/importlinter.ini"; then
		echo "[ERROR] import-linter found contract violations."
		return 1
	fi
	echo "[OK] import-linter: all contracts satisfied."
	return 0
}
###############################################################################
# Function: setup_environment
# Description: Initializes Python environment and max line length.
# Calls setup_max_line_length and setup_python_env.
###############################################################################
setup_environment() {
	setup_max_line_length
	setup_python_env
}

# Run all quality checks in CHECK mode (fail fast on first error)
run_quality_gate_check_mode() {
	# 1. Auto-fixers and formatters
	check_shfmt || exit 1
	check_isort || exit 1
	check_black || exit 1
	check_ruff || exit 1
	# 2. Fast/deterministic checks
	check_python_syntax || exit 1
	# 3. Internal policy checks
	check_no_dynamic_attrs || exit 2
	check_no_tuples || exit 3
	check_no_spanish_chars || exit 5
	# 4. Heavy/informative checks
	check_jscpd || exit 1
	check_flake8 || exit 1
	check_import_linter || exit 1
	check_mypy || exit 1
}

# Run all quality checks in APPLY mode (run all, accumulate errors, fail at end)
run_quality_gate_apply_mode() {
	local error_found=0
	# 1. Auto-fixers and formatters
	check_shfmt || error_found=1
	check_isort || error_found=1
	check_black || error_found=1
	check_ruff || error_found=1
	# 2. Fast/deterministic checks
	check_python_syntax || error_found=1
	# 3. Internal policy checks
	check_no_dynamic_attrs || error_found=2
	check_no_tuples || error_found=3
	check_no_spanish_chars || error_found=5
	# 4. Heavy/informative checks
	check_jscpd || error_found=1
	check_flake8 || error_found=1
	check_import_linter || error_found=1
	check_mypy || error_found=1
	if [ "$error_found" -ne 0 ]; then
		echo "[EXIT] Quality Gate failed (see errors above)."
		# After APPLY fails, run summary check in priority order (most important errors first)
		run_quality_gate_check_summary
		exit $error_found
	fi
}

# Summary check: runs most important checks first, fails on first error.
# This ensures the developer sees the most relevant actionable error at the end.
run_quality_gate_check_summary() {
	echo "[SUMMARY] Running prioritized checks to show the most important remaining error."
	# 1. Type checking (mypy)
	check_mypy || exit 1
	# 2. Syntax errors
	check_python_syntax || exit 1
	# 3. Ruff (lint/auto-fix)
	check_ruff || exit 1
	# 4. Flake8 (style)
	check_flake8 || exit 1
	check_import_linter || exit 1
	# 5. Policy checks
	check_no_dynamic_attrs || exit 2
	check_no_tuples || exit 3
	# 6. Spanish character check
	check_no_spanish_chars || exit 5
	# 7. Code duplication (least urgent)
	check_jscpd || exit 1
	# 8. Formatters (least urgent in summary)
	check_shfmt || exit 1
	check_isort || exit 1
	check_black || exit 1
}

main() {
	# Argument and global variable initialization
	parse_args_and_globals "$@"
	setup_environment

	# See rationale above for check order
	if [ "$CHECK_MODE" = "CHECK" ]; then
		run_quality_gate_check_mode
	else
		run_quality_gate_apply_mode
	fi

	echo "🎉 Quality Gate completed successfully!"
}

# Entrypoint
main "$@"
