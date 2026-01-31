#!/bin/bash

# ============================================================================
# QUALITY GATE SCRIPT: CHECKS AND EXECUTION MODES
# ============================================================================
#
# Usage:
#   ./quality_gate.sh [--level=LEVEL|-l LEVEL] [--check|-c|--apply] [--enforce-dynamic-attrs] [target_dir]
#
#   --level=LEVEL or -l LEVEL: Set quality level (STRICT, STANDARD, TARGET)
#   --mode=MODE or -m MODE: Set mode (CHECK, APPLY)
#   --enforce-dynamic-attrs: Enforce dynamic attrs check
#   target_dir: Directory to check (default: immich_autotag)
#
# Modes:
#   STRICT: Applies ALL checks strictly. Any error or warning in any check BLOCKS the build. Not recommended for CI unless code is perfect.
#   STANDARD: Official CI level. Applies all checks, but some only warn and DO NOT block the build (see below). El resto pueden bloquear si fallan.
#   TARGET: Intermediate mode for Quality Gate improvement branches. Blocks the build ONLY for una subset de errores. El resto se comporta como en STANDARD (warn only).
#   --enforce-dynamic-attrs  Enforce ban on getattr/hasattr (advanced).
#
# If no [target_dir] is given, defaults to the main package.
#
# =====================
# Quality Gate Checks Table (reference)
# =====================
# | Check                            | Description                                 | Strict   | Standard (CI) | Target (improvement) |
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
# * In STANDARD mode, flake8/ruff ignore E501, and mypy only warns, does not block the build.
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

# Ensure .venv/bin is in PATH for all subprocesses (import-linter, etc)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PATH="$REPO_ROOT/.venv/bin:$PATH"
PACKAGE_NAME="immich_autotag"
cd "$REPO_ROOT"

# ======================
# INTERNAL CONFIGURATION
# ======================
# Controla si quality_gate.sh se autoformatea con shfmt (1=Sí, 0=No)
FORMAT_SELF=1

###############################################################################
# Function: parse_args_and_globals
# Description: Parses command-line arguments and defines global variables.
# Globals set: QUALITY_LEVEL, CHECK_MODE, ENFORCE_DYNAMIC_ATTRS, TARGET_DIR
# Usage: parse_args_and_globals "$@"
# Returns: Exports global variables and may terminate the script in help mode
###############################################################################

# Print help/usage message (single source)
print_help() {
	echo "Usage: $0 [--level=LEVEL|-l LEVEL] [--mode=MODE|-m MODE] [--enforce-dynamic-attrs] [target_dir]"
	echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python."
	echo "  --level=LEVEL or -l LEVEL: Set quality level (STRICT, STANDARD, TARGET)"
	echo "  --mode=MODE or -m MODE: Set mode (CHECK, APPLY)"
	echo "  --enforce-dynamic-attrs: Enforce dynamic attrs check"
	echo "  target_dir: Directory to check (default: immich_autotag)"
	echo ""
	echo "Examples:"
	echo "  bash scripts/devtools/quality_gate.sh --level=TARGET --mode=CHECK"
	echo "  bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=APPLY"
}

parse_args_and_globals() {
	if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
		print_help
		exit 0
	fi

	# Local variables for parsing
	local arg check_mode quality_level enforce_dynamic_attrs target_dir next_is_level next_is_mode

	check_mode="APPLY" # Possible values: APPLY, CHECK
	quality_level=""   # Possible values: STRICT, STANDARD, TARGET
	enforce_dynamic_attrs=0
	target_dir=""
	next_is_level=0
	next_is_mode=0
	for arg in "$@"; do
		if [[ "$arg" =~ ^--level= ]]; then
			quality_level="${arg#--level=}"
		elif [ "$arg" = "-l" ]; then
			next_is_level=1
		elif [ "$next_is_level" = "1" ]; then
			quality_level="$arg"
			next_is_level=0
		elif [[ "$arg" =~ ^--mode= ]]; then
			check_mode="${arg#--mode=}"
		elif [ "$arg" = "-m" ]; then
			next_is_mode=1
		elif [ "$next_is_mode" = "1" ]; then
			check_mode="$arg"
			next_is_mode=0
		elif [ "$arg" = "--enforce-dynamic-attrs" ]; then
			enforce_dynamic_attrs=1
		elif [[ "$arg" != --* ]]; then
			# Only allow a single positional argument (target_dir)
			if [ -z "$target_dir" ]; then
				target_dir="$arg"
			else
				echo "[DEFENSIVE-FAIL] Unexpected extra positional argument: '$arg'. Only one target_dir is allowed." >&2
				exit 3
			fi
		else
			echo "[DEFENSIVE-FAIL] Unexpected argument: '$arg'. Exiting for safety." >&2
			exit 3
		fi
	done
	# Validar quality_level (defensive: all enum cases, fail on unknown)
	case "$quality_level" in
	STRICT) ;;
	STANDARD) ;;
	TARGET) ;;
	*)
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value: '$quality_level'. Must be one of: STRICT, STANDARD, TARGET." >&2
		print_help >&2
		exit 2
		;;
	esac

	# Validar check_mode (defensive: all enum cases, fail on unknown)
	case "$check_mode" in
	CHECK) ;;
	APPLY) ;;
	*)
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value: '$check_mode'. Must be one of: CHECK, APPLY." >&2
		print_help >&2
		exit 2
		;;
	esac

	# Si el usuario no fuerza quality_level, por defecto STANDARD
	if [ -z "$quality_level" ]; then
		quality_level="STANDARD"
	fi
	# If no positional argument was given, default to PACKAGE_NAME
	if [ -z "$target_dir" ]; then
		target_dir="$PACKAGE_NAME"
	fi

	# Mensajes informativos SOLO a stderr
	if [ "$quality_level" = "STRICT" ]; then
		echo "[QUALITY_LEVEL] Running in STRICT mode (all checks enforced, fail on any error)." >&2
	elif [ "$quality_level" = "STANDARD" ]; then
		echo "[QUALITY_LEVEL] Running in STANDARD mode (official CI level, some checks are warnings only)." >&2
	elif [ "$quality_level" = "TARGET" ]; then
		echo "[QUALITY_LEVEL] Running in TARGET mode (selected errors block, rest warn only)." >&2
	else
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value: '$quality_level'. Exiting for safety." >&2
		exit 99
	fi

	if [ "$check_mode" = "CHECK" ]; then
		echo "[CHECK_MODE] Running in CHECK mode (no files will be modified)." >&2
	elif [ "$check_mode" = "APPLY" ]; then
		echo "[CHECK_MODE] Running in APPLY mode (formatters may modify files)." >&2
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value: '$check_mode'. Exiting for safety." >&2
		exit 98
	fi

	# Devolver los valores como salida (en orden, SOLO datos)
	echo "$check_mode $quality_level $target_dir $enforce_dynamic_attrs"
}
# Prints a status message with common Quality Gate context (level, mode, script path)
quality_gate_status_message() {
	local msg="$1"
	echo "$msg [LEVEL: $quality_level | MODE: $check_mode | SCRIPT: $(realpath "$0")]"
}
###############################################################################
# Function: check_shfmt
# Description: Checks and formats Bash scripts using shfmt.
# Globals: CHECK_MODE
# Returns: 0 if passes, 1 if formatting errors or shfmt missing
###############################################################################
check_shfmt() {
	local check_mode="$1"
	local shfmt_exit
	echo ""
	echo "==============================="
	echo "SECTION 1: BASH SCRIPT FORMATTING CHECK (shfmt)"
	echo "==============================="
	echo ""

	local bash_scripts script_self_abs script_self_rel
	script_self_abs="$(realpath "$0")"
	script_self_rel="${script_self_abs#$PWD/}"

	# Buscar scripts, excluir quality_gate.sh si FORMAT_SELF=0
	if [ "$FORMAT_SELF" = "1" ]; then
		bash_scripts=$(find scripts -type f -name "*.sh")
	else
		bash_scripts=$(find scripts -type f -name "*.sh" | grep -v "$script_self_rel")
	fi

	# Run shfmt according to mode (defensive: enumerate all expected values)
	if [ "$check_mode" = "CHECK" ]; then
		shfmt -d -i 0 $bash_scripts
		shfmt_exit=$?
	elif [ "$check_mode" = "APPLY" ]; then
		shfmt -w -i 0 $bash_scripts
		shfmt_exit=$?
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value in check_shfmt: '$check_mode'. Exiting for safety." >&2
		exit 97
	fi
	if [ $shfmt_exit -ne 0 ]; then
		echo "[WARNING] shfmt reported issues."
		if [ "$check_mode" = "CHECK" ]; then
			echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
			return 1
		fi
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
		echo "[WARN] Could not extract line-length from pyproject.toml, using 88 by default." >&2
		max_line_length_local=88
	fi
	echo "$max_line_length_local"
}

###############################################################################
# Function: setup_python_env
# Description: Activates the project virtual environment or uses system Python.
# Globals set: PY_BIN
# Returns: nothing, but exports PY_BIN or exits if no Python is available
###############################################################################
setup_python_venv_env() {
	local venv_activate="$REPO_ROOT/.venv/bin/activate"
	echo "[INFO] Ejecutando setup_venv.sh --dev para asegurar el entorno y dependencias..." >&2
	if [ -f "$REPO_ROOT/setup_venv.sh" ]; then
		chmod +x "$REPO_ROOT/setup_venv.sh"
		bash "$REPO_ROOT/setup_venv.sh" --dev >&2
	else
		echo "[ERROR] setup_venv.sh not found at $REPO_ROOT. Cannot set up development environment." >&2
		exit 1
	fi
	local py_bin
	if [ -f "$venv_activate" ]; then
		# Use project venv when available
		source "$venv_activate"
		py_bin="$REPO_ROOT/.venv/bin/python"
	else
		echo "[WARN] .venv not found at $REPO_ROOT/.venv — falling back to system python (this may install tools globally)." >&2
		py_bin="$(command -v python3 || command -v python)"
		if [ -z "$py_bin" ]; then
			echo "[ERROR] No python executable found. Create a virtualenv at .venv or install python3." >&2
			exit 1
		fi
	fi
	echo "$py_bin"
}

###############################################################################
# Function: check_python_syntax
# Description: Compiles Python files to detect syntax errors.
# Globals: PY_BIN, TARGET_DIR
# Returns: 0 if passes, 1 if syntax errors
###############################################################################
check_python_syntax() {
	local py_bin="$1"
	local target_dir="$2"
	echo "Checking for syntax and indentation errors..."
	echo "[CHECK] Byte-compiling Python sources in $target_dir..."
	# Buscar y compilar todos los .py fuera de carpetas ignoradas
	local failed=0
	find "$target_dir" \
		\( -path "$target_dir/.venv" -o -path "$target_dir/immich-client" -o -path "$target_dir/scripts" -o -path "$target_dir/jenkins_logs" \) -prune -false -o -name "*.py" -print |
		while read -r file; do
			if ! "$py_bin" -m py_compile "$file"; then
				echo "[ERROR] Syntax error in $file"
				failed=1
			fi
		done
	if [ "$failed" -ne 0 ]; then
		echo "[ERROR] Byte-compilation failed (syntax error or import-time failure). Aborting."
		return 1
	fi
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
ensure_python_tool() {
	local py_bin="$1"
	local tool_import_check="$2"
	local tool_pkg="$3"
	if ! "$py_bin" -c "import ${tool_import_check}" 2>/dev/null; then
		echo "Installing ${tool_pkg} into environment ($py_bin)..."
		"$py_bin" -m pip install "${tool_pkg}"
	fi
}

###############################################################################
# Function: check_isort
# Description: Sorts Python imports using isort.
# Globals: CHECK_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 if passes, 1 if sorting issues
###############################################################################
check_isort() {
	local check_mode="$1"
	local py_bin="$2"
	local max_line_length="$3"
	local target_dir="$4"
	local isort_skips isort_exit
	ensure_python_tool "$py_bin" isort isort
	isort_skips="--skip .venv --skip immich-client --skip scripts --skip jenkins_logs --line-length $max_line_length"
	if [ "$check_mode" = "CHECK" ]; then
		"$py_bin" -m isort $isort_skips --profile black --check-only "$target_dir"
		isort_exit=$?
	elif [ "$check_mode" = "APPLY" ]; then
		"$py_bin" -m isort $isort_skips --profile black "$target_dir"
		isort_exit=$?
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value in check_isort: '$check_mode'. Exiting for safety." >&2
		exit 96
	fi
	if [ $isort_exit -ne 0 ]; then
		echo "[WARNING] isort reported issues."
		if [ "$check_mode" = "CHECK" ]; then
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
	local check_mode="$1"
	local target_dir="$2"
	local ssort_failed=0
	ensure_ssort
	if [ "$check_mode" = "CHECK" ]; then
		echo "[FORMAT] Running ssort in CHECK mode..."
		ssort --check "$target_dir" || ssort_failed=1
	elif [ "$check_mode" = "APPLY" ]; then
		echo "[FORMAT] Running ssort in APPLY mode..."
		ssort "$target_dir" || ssort_failed=1
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value in check_ssort: '$check_mode'. Exiting for safety." >&2
		exit 95
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
# Globals: CHECK_MODE, STANDARD_MODE, PY_BIN, TARGET_DIR
# Returns: 0 if passes, 1 if style issues
###############################################################################
check_ruff() {
	local check_mode="$1"
	local py_bin="$2"
	local max_line_length="$3"
	local target_dir="$4"
	local ruff_ignore="" ruff_exit
	ensure_python_tool "$py_bin" ruff ruff

	# Recoge quality_level solo del parámetro (quinto argumento)
	local quality_level="$5"
	if [ -z "$quality_level" ]; then
		quality_level="STANDARD"
	fi

	if [ "$quality_level" = "STANDARD" ]; then
		ruff_ignore="--ignore E501"
		echo "[$quality_level MODE] Ruff will ignore E501 (line length) and will NOT block the build for it. Only F821 errors will block the build."
	elif [ "$quality_level" = "TARGET" ]; then
		ruff_ignore="--ignore E501"
		echo "[$quality_level MODE] Ruff will ignore E501 (line length) and will NOT block the build for it. Only F821 errors will block the build."
	elif [ "$quality_level" = "STRICT" ]; then
		ruff_ignore=""
		echo "[STRICT MODE] Ruff will NOT ignore any errors. All errors will block the build."
	else
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value in check_ruff: '$quality_level'. Exiting for safety."
		exit 94
	fi

	local ruff_output ruff_exit
	if [ "$check_mode" = "CHECK" ]; then
		ruff_output=$("$py_bin" -m ruff check --fix $ruff_ignore "$target_dir" 2>&1)
		ruff_exit=$?
	else
		ruff_output=$("$py_bin" -m ruff check --fix $ruff_ignore "$target_dir" 2>&1)
		ruff_exit=$?
	fi

	if [ "$quality_level" = "STANDARD" ] || [ "$quality_level" = "TARGET" ]; then
		local f821_count
		f821_count=$(echo "$ruff_output" | grep -c 'F821')
		if [ "$f821_count" -gt 0 ]; then
			echo "[$quality_level MODE: F821 ONLY] Found $f821_count F821 (undefined name) errors:"
			echo "$ruff_output" | grep 'F821'
			return 1
		else
			echo "[$quality_level MODE: F821 ONLY] No F821 errors found."
			return 0
		fi
	elif [ "$quality_level" = "STRICT" ]; then
		if [ $ruff_exit -ne 0 ]; then
			echo "$ruff_output"
			echo "[WARNING] ruff reported/fixed issues."
			if [ "$check_mode" = "CHECK" ]; then
				echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
				return 1
			fi
		fi
	else
		echo "[ERROR] Invalid quality_level: $quality_level. Must be one of: STRICT, STANDARD, TARGET."
		return 2
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
	local check_mode="$1"
	local py_bin="$2"
	local max_line_length="$3"
	local target_dir="$4"
	ensure_python_tool "$py_bin" black black
	if [ "$check_mode" = "CHECK" ]; then
		"$py_bin" -m black --check --line-length "$max_line_length" "$target_dir"
		black_exit=$?
	else
		"$py_bin" -m black --line-length "$max_line_length" "$target_dir"
		black_exit=$?
	fi
	if [ $black_exit -ne 0 ]; then
		echo "[WARNING] black reported issues."
		if [ "$check_mode" = "CHECK" ]; then
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
	local py_bin="$1"
	local repo_root="$2"
	local target_dir="$3"
	echo "[CHECK] Disallow tuple returns and tuple-typed class members (project policy)"
	"$py_bin" "${repo_root}/scripts/devtools/check_no_tuples.py" "$target_dir" --exclude ".venv,immich-client,scripts" || {
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
	$jscmd --silent --min-tokens 30 --max-lines 100 --format python --ignore "**/.venv/**,**/immich-client/**,**/scripts/**" "$1"
	jscpd_exit=$?
	if [ $jscpd_exit -ne 0 ]; then
		echo "[ERROR] jscpd detected code duplication. Please refactor duplicate code."
		echo "🤔 Déjà vu? jscpd saw something twice... Time to refactor!"
		return 1
	fi
	echo "jscpd check passed: no significant code duplication detected."
	return 0
}

###############################################################################
# Function: check_flake8
# Description: Lint for Python style and errors using flake8.
# Globals: STANDARD_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 if passes, 1 if style errors
###############################################################################
check_flake8() {
	local check_mode="$1"
	local quality_level="$2"
	local py_bin="$3"
	local max_line_length="$4"
	local target_dir="$5"
	local flake_failed=0 flake8_ignore
	ensure_python_tool "$py_bin" flake8 flake8
	flake8_ignore="E203,W503"
	if [ "$quality_level" = "STRICT" ]; then
		: # No se hace nada especial
	elif [ "$quality_level" = "STANDARD" ]; then
		flake8_ignore="$flake8_ignore,E501"
		echo "[NON-STRICT MODE] E501 (line length) errors are ignored and will NOT block the build."
	elif [ "$quality_level" = "TARGET" ]; then
		flake8_ignore="$flake8_ignore,E501"
		echo "[NON-STRICT MODE] E501 (line length) errors are ignored and will NOT block the build."
	else
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value in check_flake8: '$quality_level'. Exiting for safety."
		return 93
	fi
	echo "[INFO] Running flake8 (output below if any):"
	"$py_bin" -m flake8 --max-line-length=$max_line_length --extend-ignore=$flake8_ignore --exclude=.venv,immich-client,scripts,jenkins_logs "$target_dir"
	if [ $? -ne 0 ]; then
		flake_failed=1
	fi
	if [ $flake_failed -ne 0 ]; then
		if [ "$quality_level" = "STRICT" ]; then
			echo "[ERROR] flake8 failed. See output above."
			return 1
		elif [ "$quality_level" = "STANDARD" ]; then
			echo "[WARNING] flake8 failed, but STANDARD mode is enabled. See output above."
			echo "[STANDARD MODE] Not blocking build on flake8 errors."
		elif [ "$quality_level" = "TARGET" ]; then
			echo "[WARNING] flake8 failed, but TARGET mode is enabled. See output above."
			echo "[TARGET MODE] Not blocking build on flake8 errors."
		else
			echo "[ERROR] Invalid quality level: $quality_level. Must be one of: STRICT, STANDARD, TARGET."
			return 2
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
	local check_mode="$1"
	local quality_level="$2"
	local py_bin="$3"
	local target_dir="$4"
	local mypy_failed=0 mypy_output mypy_exit_code mypy_error_count mypy_files_count
	ensure_python_tool "$py_bin" mypy mypy
	echo "[INFO] Running mypy (output below if any):"
	set +e
	mypy_output=$($py_bin -m mypy --ignore-missing-imports "$target_dir" 2>&1)
	mypy_exit_code=$?
	set -e
	if [ $mypy_exit_code -ne 0 ]; then
		mypy_failed=1
	fi
	if [ $mypy_failed -ne 0 ]; then
		echo "$mypy_output"
		mypy_error_count=$(echo "$mypy_output" | grep -c 'error:')
		mypy_files_count=$(echo "$mypy_output" | grep -o '^[^:]*:' | cut -d: -f1 | sort | uniq | wc -l)
		echo "[ERROR] MYPY FAILED. TOTAL ERRORS: $mypy_error_count IN $mypy_files_count FILES."
		echo "[INFO] Command executed: $py_bin -m mypy --ignore-missing-imports $target_dir"
		if [ "$quality_level" = "STRICT" ]; then
			# En modo estricto, cualquier error de mypy bloquea
			echo '[STRICT MODE] Any mypy error blocks the build.'
			echo '[EXIT] Quality Gate failed due to mypy errors.'
			return 1
		elif [ "$quality_level" = "STANDARD" ]; then
			# Solo bloquea por errores arg-type y call-arg (objetivo mínimo)
			mypy_block_count=$(echo "$mypy_output" | grep -E '\[(arg-type|call-arg)\]' | wc -l)
			if [ "$mypy_block_count" -gt 0 ]; then
				quality_gate_status_message "\n\n❌❌❌ QUALITY GATE BLOCKED ($quality_level) ❌❌❌
🚨 MYPY: $mypy_block_count CRITICAL ERRORS (ARG-TYPE/CALL-ARG) DETECTED 🚨
[EXIT] QUALITY GATE FAILED DUE TO CRITICAL MYPY ERRORS."
				return 1
			else
				echo "[STANDARD MODE] Only non-critical mypy errors found (return-value, attr-defined, imports, etc). Not blocking build.'"
			fi
		elif [ "$quality_level" = "TARGET" ]; then
			# Bloquea por errores arg-type, call-arg y attr-defined
			mypy_block_count=$(echo "$mypy_output" | grep -E '\[(arg-type|call-arg|attr-defined)\]' | wc -l)
			if [ "$mypy_block_count" -gt 0 ]; then
				quality_gate_status_message "\n\n❌❌❌ QUALITY GATE BLOCKED ($quality_level) ❌❌❌
🚨 MYPY: $mypy_block_count CRITICAL ERRORS (ARG-TYPE/CALL-ARG/ATTR-DEFINED) DETECTED 🚨
[EXIT] QUALITY GATE FAILED DUE TO CRITICAL MYPY ERRORS."
				return 1
			else
				echo "[TARGET MODE] Only non-critical mypy errors found (return-value, imports, etc). Not blocking build.'"
			fi
		else
			echo "[ERROR] Invalid quality level: $quality_level. Must be one of: STRICT, STANDARD, TARGET."
			return 2
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
	local SPANISH_WORDS='aquellas
aquellos
antes
cam-biando
cambiado
cierto
claro
comentario
complicado
complejo
compatibilidad
correcto
devuelve
devolviendo
durante
ejemplo
entonces
estructura
etiqueta
etiquetas
falso
grande
hoy
imposible
importante
improbable
inicio
interesante
limpieza
lista
lento
luego
mantenimiento
mayor
mejor
menos
mientras
muy
nombre
nuevo
nueva
nuevas
nuevos
nunca
oscuro
peor
posible
primera
primeras
primero
primeros
probable
referencia
seguro
sencillo
si
siempre
soporta
tenemos
usamos
verdadero
vieja
viejas
viejo
viejos'

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
	spanish_matches=$(echo "$files_to_check" | xargs grep -n -I -i -E "$SPANISH_PATTERN" || true)

	if [ -n "$spanish_matches" ]; then
		echo '❌ Spanish language characters detected in the following files/lines:'
		echo "$spanish_matches"
		# Count matches and affected files
		local match_count file_count
		match_count=$(echo "$spanish_matches" | grep -c '^')
		file_count=$(echo "$spanish_matches" | cut -d: -f1 | sort | uniq | wc -l)
		echo "Total matches: $match_count | Files affected: $file_count"
		quality_gate_status_message "[EXIT] Quality Gate failed due to forbidden Spanish characters."
		quality_gate_status_message "Build failed: Please remove all Spanish text and accents before publishing."
		quality_gate_status_message "¡Ay caramba! Spanish detected. Let's keep it English, amigos!"
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
	local repo_root="$1"
	local py_bin
	# Detectar el binario de Python del entorno virtual
	if [ -f "$repo_root/.venv/bin/python" ]; then
		py_bin="$repo_root/.venv/bin/python"
	else
		py_bin="$(command -v python3 || command -v python)"
	fi
	echo "[CHECK] Running import-linter (lint-imports) for architectural contracts..."
	# Asegurar que import-linter está instalado
	if ! "$py_bin" -c "import importlinter" 2>/dev/null; then
		echo "[INFO] import-linter not found in environment. Installing..."
		"$py_bin" -m pip install import-linter
	fi
	# Ejecutar import-linter usando el binario real del entorno virtual o PATH
	# alternativa: "$py_bin" -m importlinter
	local lint_imports_bin
	if [ -n "$VIRTUAL_ENV" ] && [ -x "$VIRTUAL_ENV/bin/lint-imports" ]; then
		lint_imports_bin="$VIRTUAL_ENV/bin/lint-imports"
	elif [ -x "$repo_root/.venv/bin/lint-imports" ]; then
		lint_imports_bin="$repo_root/.venv/bin/lint-imports"
	else
		lint_imports_bin="$(command -v lint-imports)"
	fi
	if [ -z "$lint_imports_bin" ]; then
		echo "[ERROR] lint-imports binary not found in virtualenv or PATH."
		return 1
	fi
	if ! "$lint_imports_bin" --config "$repo_root/importlinter.ini"; then
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

# Run all quality checks in CHECK mode (fail fast on first error)
run_quality_gate_check_mode() {
	local py_bin="$1"
	local max_line_length="$2"
	local target_dir="$3"
	local quality_level="$4"
	local check_mode="$5"
	local repo_root="$6"
	local enforce_dynamic_attrs="$7"

	# All implemented check modules are called below. If a check is not called, it is either deprecated, not implemented, or not relevant for this mode. Add new checks here as needed.
	# 1. Blocking checks (fail fast on first error)
	check_python_syntax "$py_bin" "$target_dir" || exit 1
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || exit 1
	check_jscpd "$target_dir" || exit 1
	check_import_linter "$repo_root" || exit 1
	check_no_dynamic_attrs "$enforce_dynamic_attrs" "$target_dir" || exit 2
	check_no_tuples "$py_bin" "$repo_root" "$target_dir" || exit 3
	check_no_spanish_chars "$target_dir" || exit 5
	# 2. Formatters and style (run only if all blocking checks pass)
	check_shfmt "$check_mode" "$target_dir" || exit 1
	check_isort "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || exit 1
	check_ssort "$check_mode" "$target_dir" || exit 1
	check_black "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || exit 1
	check_ruff "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" || exit 1
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || exit 1
}

# Run all quality checks in APPLY mode (run all, accumulate errors, fail at end)
run_quality_gate_apply_mode() {
	local py_bin="$1"
	local max_line_length="$2"
	local target_dir="$3"
	local quality_level="$4"
	local check_mode="$5"
	local repo_root="$6"
	local enforce_dynamic_attrs="$7"
	local error_found=0
	# All implemented check modules are called below. If a check is not called, it is either deprecated, not implemented, or not relevant for this mode. Add new checks here as needed.
	# 1. Auto-fixers and formatters
	check_shfmt "$check_mode" "$target_dir" || error_found=1
	check_isort "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || error_found=1
	check_ssort "$check_mode" "$target_dir" || error_found=1
	check_black "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || error_found=1
	check_ruff "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" || error_found=1
	# 2. Fast/deterministic checks
	check_python_syntax "$py_bin" "$target_dir" || error_found=1
	# 3. Internal policy checks
	check_no_dynamic_attrs "$enforce_dynamic_attrs" "$target_dir" || error_found=2
	check_no_tuples "$py_bin" "$repo_root" "$target_dir" || error_found=3
	check_no_spanish_chars "$target_dir" || error_found=5
	# 4. Heavy/informative checks
	check_jscpd "$target_dir" || error_found=1
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || error_found=1
	check_import_linter "$repo_root" || error_found=1
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || error_found=1
	if [ "$error_found" -ne 0 ]; then
		quality_gate_status_message "[EXIT] Quality Gate failed (see errors above)."
		# After APPLY fails, run summary check in priority order (most important errors first)
		run_quality_gate_check_summary "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$repo_root" "$enforce_dynamic_attrs"
		exit $error_found
	fi
}

# Summary check: runs most important checks first, fails on first error.
# This ensures the developer sees the most relevant actionable error at the end.
run_quality_gate_check_summary() {
	local py_bin="$1"
	local max_line_length="$2"
	local target_dir="$3"
	local quality_level="$4"
	local check_mode="$5"
	local repo_root="$6"
	local enforce_dynamic_attrs="$7"
	echo "[SUMMARY] Running prioritized checks to show the most important remaining error."
	# All implemented check modules are called below in priority order. If a check is not called, it is either deprecated, not implemented, or not relevant for this summary mode. Add new checks here as needed.
	# 1. Checks we have already passed (quality threshold):
	#    We put first the checks that we have already passed (like the language check),
	#    so that if they break, it is very obvious and immediately visible.
	#    This way we avoid quality deterioration in aspects that are already under control.
	check_no_spanish_chars "$target_dir" || exit 5
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || exit 1
	# 2. Syntax errors
	check_python_syntax "$py_bin" "$target_dir" || exit 1
	# 3. Ruff (lint/auto-fix)
	check_ruff "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" || exit 1
	# 4. Flake8 (style)
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || exit 1
	check_import_linter "$repo_root" || exit 1
	# 5. Policy checks
	check_no_dynamic_attrs "$enforce_dynamic_attrs" "$target_dir" || exit 2
	check_no_tuples "$py_bin" "$repo_root" "$target_dir" || exit 3
	# 6. Spanish character check
	# 7. Code duplication (least urgent)
	check_jscpd "$target_dir" || exit 1
	# 8. Formatters (least urgent in summary)
	check_shfmt "$check_mode" "$target_dir" || exit 1
	check_isort "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || exit 1
	check_ssort "$check_mode" "$target_dir" || exit 1
	check_black "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || exit 1
}

# Refactor: main usa solo variables locales y pasa los valores explícitamente
main() {
	# Argument and global variable initialization
	local check_mode quality_level target_dir enforce_dynamic_attrs max_line_length py_bin
	read -r check_mode quality_level target_dir enforce_dynamic_attrs < <(parse_args_and_globals "$@")
	max_line_length=$(setup_max_line_length)
	py_bin=$(setup_python_venv_env)

	# Pasar los valores explícitamente a las funciones de chequeo
	# All quality gate modules/checks are called via run_quality_gate_check_mode and run_quality_gate_apply_mode.
	# If a check is not called, it is either deprecated or not implemented yet. Add new checks to those functions.
	if [ "$check_mode" = "CHECK" ]; then
		run_quality_gate_check_mode "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$repo_root" "$enforce_dynamic_attrs"
	elif [ "$check_mode" = "APPLY" ]; then
		run_quality_gate_apply_mode "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$repo_root" "$enforce_dynamic_attrs"
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value in main: '$check_mode'. Exiting for safety." >&2
		exit 92
	fi

	quality_gate_status_message "🎉 Quality Gate completed successfully!"
	quality_gate_status_message "All checks passed! Your code is cleaner than a robot's hard drive."
}

# Entrypoint
main "$@"
