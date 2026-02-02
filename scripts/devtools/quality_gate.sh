#!/bin/bash

# ============================================================================
# QUALITY GATE SCRIPT: CHECKS AND EXECUTION MODES
# ============================================================================
#
# Usage:
#   ./quality_gate.sh [--level=LEVEL|-l LEVEL] [--mode=MODE|-m MODE] [--only-check=FUNC] [target_dir]
#
#   --level=LEVEL or -l LEVEL: Set quality level (STRICT, STANDARD, TARGET)
#   --mode=MODE or -m MODE: Set mode (CHECK, APPLY)
#   --only-check=FUNC: Run only the specified check function (e.g., check_black, check_mypy, etc.)
#   target_dir: Directory to check (default: immich_autotag)
#
# Modes:
#   STRICT: Applies ALL checks strictly. Any error or warning in any check BLOCKS the build. Not recommended for CI unless code is perfect.
#   STANDARD: Official CI level. Applies all checks, but some only warn and DO NOT block the build (see below). The rest may block if they fail.
#   TARGET: Intermediate mode for Quality Gate improvement branches. Blocks the build ONLY for una subset de errores. El resto se comporta como en STANDARD (warn only).
#
# If no [target_dir] is given, defaults to the main package.
#
# =====================
# Table 1: Quality Gate Bash Functions Table (reference)
# =====================
# | #  | Bash Function           | Origin                | Short Description                                 | Strict   | Standard (CI)                | Target (improvement)         |
# |----|------------------------|-----------------------|---------------------------------------------------|----------|------------------------------|------------------------------|
# | 1  | check_python_syntax    | stdlib (python)       | Checks Python syntax/indentation errors           | Blocks on any error           | Blocks on any error           | Blocks on any error           |
# | 2  | check_ruff             | pip (ruff)            | Lint and autoformat with ruff                     | Blocks any error              | Blocks all (E501 ignored)     | Blocks all (E501 ignored)     |
# | 3  | check_isort            | pip (isort)           | Sorts imports with isort                          | Blocks if unsorted            | Blocks if unsorted            | Blocks if unsorted            |
# | 4  | check_black            | pip (black)           | Formats code with black                           | Blocks if changes             | Blocks if changes             | Blocks if changes             |
# | 5  | check_flake8           | pip (flake8)          | Style linter with flake8                          | Blocks any error              | Blocks all (E501 ignored)     | Blocks all (E501 ignored)     |
# | 6  | check_mypy             | pip (mypy)            | Static type checking with mypy                    | Blocks any error              | Only arg-type/call-arg block, rest warning | arg-type/call-arg/attr-defined block, rest warning |
# | 7  | check_ssort            | pip (ssort, github)   | Deterministic class method ordering               | Blocks if unordered           | Blocks if unordered**         | Blocks if unordered**         |
# | 8  | check_no_tuples        | custom (python)       | Forbids tuples as return/attribute                | Blocks if tuples detected     | Blocks if tuples detected     | Blocks if tuples detected     |
# | 9  | check_jscpd            | npx (jscpd)           | Detects code duplication                          | Blocks if duplicates found    | Blocks if duplicates found    | Blocks if duplicates found    |
# | 10 | check_no_spanish_chars | custom (bash/grep)    | Forbids Spanish chars/text                        | Blocks if Spanish detected    | Blocks if Spanish detected    | Blocks if Spanish detected    |
# | 11 | check_import_linter    | pip (import-linter)   | Verifies architectural import contracts           | Blocks if violations          | Blocks if violations          | Blocks if violations          |
# | 12 | check_no_dynamic_attrs | custom (bash/grep)    | Forbids getattr/hasattr (static typing)           | Blocks if found   | Blocks if found   | Blocks if found   |
# | 13 | check_shfmt            | debian/pip (shfmt)    | Formats bash scripts with shfmt                   | Blocks if changes             | Blocks if changes             | Blocks if changes             |
#
# =====================
# Quality Gate Checks Table (reference)
# =====================
# =====================
# Table 2: Quality Gate Logical Checks Table (reference)
# =====================
# | #  | Check Name                              | Bash Function           | Description                                 | Strict   | Standard (CI)                | Target (improvement)         |
# |----|-----------------------------------------|------------------------|---------------------------------------------|----------|------------------------------|------------------------------|
# | 1  | Syntax/Indent (compileall)              | check_python_syntax    | Python syntax errors                        |   ✔️     |   ✔️                         |   ✔️                        |
# | 2  | ruff (lint/auto-fix)                    | check_ruff             | Linter and auto-format                      |   ✔️     |   All errors (E501 ignored)  |   All errors (E501 ignored)  |
# | 3  | isort (import sorting)                  | check_isort            | Sorts imports                               |   ✔️     |   ✔️                         |   ✔️                        |
# | 4  | black (formatter)                       | check_black            | Code formatter                              |   ✔️     |   ✔️                         |   ✔️                        |
# | 5  | flake8 (style)                          | check_flake8           | Style linter                                |   ✔️     |   All errors (E501 ignored)  |   All errors (E501 ignored) |
# | 6  | flake8 (E501 long lines)                | check_flake8           | Line length                                 |   ✔️     |   Ignored                   |   Ignored                   |
# | 7  | ruff (E501 long lines)                  | check_ruff             | Line length                                 |   ✔️     |   Ignored                   |   Ignored                   |
# | 8  | mypy (type check)                       | check_mypy             | Type checking (all errors)                  |   ✔️     |   ✔️                         |   ✔️                        |
# | 11 | ssort (method order)                    | check_ssort            | Class method ordering                       |   ✔️**   |   ✔️**                       |   ✔️**                      |
# | 12 | tuple return/type policy                | check_no_tuples        | Forbids tuples as return/attribute          |   ✔️     |   ✔️                         |   ✔️                        |
# | 13 | jscpd (code duplication)                | check_jscpd            | Detects code duplication                    |   ✔️     |   ✔️                         |   ✔️                        |
# | 14 | Spanish character check                 | check_no_spanish_chars | Forbids Spanish text/accents                |   ✔️     |   ✔️                         |   ✔️                        |
# | 15 | import-linter (contracts)               | check_import_linter    | Architectural import contracts              |   ✔️     |   ✔️                         |   ✔️                        |
# | 16 | no dynamic attrs (getattr/hasattr)      | check_no_dynamic_attrs | Forbids getattr/hasattr for static typing   |   ✔️   |   ❌                       |   ✔️                      |
# | 17 | no tuples (returns/attributes)          | check_no_tuples        | Forbids tuples as return/attribute          |   ✔️     |   ✔️                         |   ✔️                        |
# | 18 | shfmt (bash formatting)                 | check_shfmt            | Bash script formatting                      |   ✔️     |   ✔️                         |   ✔️                        |
# -----------------------------------------------------------------------------
# * In STANDARD and TARGET mode, flake8/ruff ignore E501. STANDARD and TARGET block ALL flake8/ruff errors (except E501). Mypy blocks ALL errors in both modes.
# ** Dynamic attributes check is ENABLED for STRICT and TARGET (always), but DISABLED for STANDARD.
#
# =====================
# Quality Gate Objectives Table (current/future)
# =====================
# | Objective (subset/block)          | Status      | Plan/Notes                       |
# |-----------------------------------|-------------|----------------------------------|
# | mypy (all errors)                 | ✅ COMPLETED | All mypy errors now block in STANDARD/TARGET |
# | ruff (all errors except E501)     | ✅ COMPLETED | STANDARD/TARGET block all ruff   |
# | flake8 (all errors except E501)   | ✅ COMPLETED | STANDARD/TARGET block all flake8 |
# | Spanish character check           | Future      | Warn only, will block in future  |
# | flake8/ruff E501                  | Future      | Ignored, will block in future    |
#

set -x
set -e
set -o pipefail

# Store the original command for reproducibility
QUALITY_GATE_COMMAND="$0 $*"

# Trap for unexpected errors to always print a clear message before exit
trap 'if [ $? -ne 0 ]; then echo "[FATAL] Quality Gate aborted unexpectedly. Check the output above for details."; quality_gate_print_reproduced_command; fi' EXIT

# Ensure .venv/bin is in PATH for all subprocesses (import-linter, etc)
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 && pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PATH="$REPO_ROOT/.venv/bin:$PATH"
PACKAGE_NAME="immich_autotag"
cd "$REPO_ROOT"

# ======================
# INTERNAL CONFIGURATION
# ======================
# Controls if quality_gate.sh is autoformatted with shfmt (1=Yes, 0=No)
FORMAT_SELF=1

###############################################################################
# Function: parse_args_and_globals
# Description: Parses command-line arguments and defines global variables.
# Globals set: QUALITY_LEVEL, CHECK_MODE, TARGET_DIR
# Usage: parse_args_and_globals "$@"
# Returns: Exports global variables and may terminate the script in help mode
###############################################################################

# Print help/usage message (single source)
print_help() {
	echo "Usage: $0 [--level=LEVEL|-l LEVEL] [--mode=MODE|-m MODE] [--only-check=FUNC] [target_dir]"
	echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python."
	echo "  --level=LEVEL or -l LEVEL: Set quality level (STRICT, STANDARD, TARGET)"
	echo "  --mode=MODE or -m MODE: Set mode (CHECK, APPLY)"
	echo "  --only-check=FUNC: Run only the specified check function (e.g., check_black, check_mypy, etc.)"
	echo "  target_dir: Directory to check (default: immich_autotag)"
	echo ""
	echo "Examples:"
	echo "  bash scripts/devtools/quality_gate.sh --level=TARGET --mode=CHECK --only-check=check_black"
	echo "  bash scripts/devtools/quality_gate.sh --level=STANDARD --mode=APPLY"
}

parse_args_and_globals() {
	if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
		print_help
		exit 0
	fi

	# Local variables for parsing
	local arg check_mode quality_level target_dir only_check next_is_level next_is_mode

	check_mode="APPLY" # Possible values: APPLY, CHECK
	quality_level=""   # Possible values: STRICT, STANDARD, TARGET
	target_dir=""
	only_check=""
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
		elif [[ "$arg" =~ ^--only-check= ]]; then
			only_check="${arg#--only-check=}"
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

	# If the user does not force quality_level, default to STANDARD
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
	echo "$check_mode $quality_level $target_dir $only_check"
}
# Prints a status message with common Quality Gate context (level, mode, script path)
quality_gate_status_message() {
	local msg="$1"
	echo "$msg [LEVEL: $quality_level | MODE: $check_mode | SCRIPT: $(realpath "$0")]"
}

###############################################################################
# Function: quality_gate_print_command
# Description: Prints the exact command that will be executed (for reproducibility).
# Usage: quality_gate_print_command "command" "arg1" "arg2" ...
# Returns: nothing, prints to stdout
###############################################################################
quality_gate_print_command() {
	echo ""
	echo "[COMMAND] Executing:"
	printf '  '
	printf '%s ' "$@"
	echo ""
	echo ""
}

###############################################################################
# Function: quality_gate_print_reproduced_command
# Description: Prints the exact command that was originally executed for reproducibility.
# This is printed at the end of execution or when errors occur.
# Globals: QUALITY_GATE_COMMAND
# Returns: nothing, prints to stdout/stderr
###############################################################################
quality_gate_print_reproduced_command() {
	echo ""
	echo "═══════════════════════════════════════════════════════════════════════════════"
	echo "[REPRODUCIBLE COMMAND] To reproduce this exact execution, run:"
	echo ""
	printf '  %s\n' "$QUALITY_GATE_COMMAND"
	echo ""
	echo "═══════════════════════════════════════════════════════════════════════════════"
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

	# Find scripts, exclude quality_gate.sh if FORMAT_SELF=0
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
		return 97
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
		return 1
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
			return 1
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
		return 96
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
		return 95
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

	# Collects quality_level only from the parameter (fifth argument)
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
		return 94
	fi

	local ruff_output ruff_exit
	if [ "$check_mode" = "CHECK" ]; then
		ruff_output=$("$py_bin" -m ruff check $ruff_ignore "$target_dir" 2>&1)
		ruff_exit=$?
	else
		ruff_output=$("$py_bin" -m ruff check --fix $ruff_ignore "$target_dir" 2>&1)
		ruff_exit=$?
	fi

	if [ "$quality_level" = "STANDARD" ] || [ "$quality_level" = "TARGET" ]; then
		# OPTION #2 ACTIVATED: Block all ruff errors (except E501)
		if [ $ruff_exit -ne 0 ]; then
			echo "$ruff_output"
			echo "[$quality_level MODE] Ruff found errors (E501 ignored)."
			if [ "$check_mode" = "CHECK" ]; then
				echo "Run in apply mode to let ruff attempt to fix issues."
				return 1
			fi
			return 1
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
# Parameters: target_dir, quality_level
# Returns: 0 if passes, 1 if forbidden uses detected
###############################################################################
check_no_dynamic_attrs() {
	local target_dir="$1"
	local quality_level="$2"
	local matches
	# Policy enforcement: disallow dynamic attribute access via getattr() and hasattr()
	# Projects following our coding guidelines avoid these calls because they
	# undermine static typing and hide missing attributes. This check is strict.
	# - ENABLED for STANDARD, TARGET and STRICT
	local should_enforce=0
	case "$quality_level" in
	STANDARD | TARGET | STRICT)
		should_enforce=1
		;;
	*)
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value in check_no_dynamic_attrs: '$quality_level'. Exiting for safety." >&2
		return 91
		;;
	esac
	if [ "$should_enforce" -eq 1 ]; then
		matches=$(grep -R --line-number --exclude-dir=".venv" --exclude-dir="immich-client" --exclude-dir="scripts" --include="*.py" -E "getattr\(|hasattr\(" "$target_dir" || true)
		if [ -n "$matches" ]; then
			echo "$matches"
			echo "[ERROR] Forbidden use of getattr(...) or hasattr(...) detected. Our style policy bans dynamic attribute access."
			echo "Fix occurrences in source (do not rely on getattr/hasattr)."
			return 1
		fi
		echo "[$quality_level MODE] getattr/hasattr policy enforcement is ENABLED."
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
	"$py_bin" "$repo_root/scripts/devtools/check_no_tuples.py" "$target_dir" --exclude ".venv,immich-client,scripts" || {
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
		echo "🤔 Already seen? jscpd saw something twice... Time to refactor!"
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
	local flake_failed=0 flake8_ignore flake8_select
	ensure_python_tool "$py_bin" flake8 flake8
	flake8_ignore="E203,W503"
	if [ "$quality_level" = "STRICT" ]; then
		: # No se hace nada especial
	elif [ "$quality_level" = "STANDARD" ]; then
		flake8_ignore="$flake8_ignore,E501"
		# OPTION #3 ACTIVATED: Block all flake8 errors (not just F*), except E501
		echo "[STANDARD MODE] E501 (line length) errors are ignored. All other errors will block the build."
	elif [ "$quality_level" = "TARGET" ]; then
		flake8_ignore="$flake8_ignore,E501"
		# OPTION #3 ACTIVATED: Block all flake8 errors (not just F*), except E501
		echo "[TARGET MODE] E501 (line length) errors are ignored. All other errors will block the build."
	else
		echo "[DEFENSIVE-FAIL] Unexpected quality_level value in check_flake8: '$quality_level'. Exiting for safety."
		return 93
	fi
	echo "[INFO] Running flake8 (output below if any):"
	if [ -n "$flake8_select" ]; then
		"$py_bin" -m flake8 --max-line-length=$max_line_length --select=$flake8_select --extend-ignore=$flake8_ignore --exclude=.venv,immich-client,scripts,jenkins_logs "$target_dir"
	else
		"$py_bin" -m flake8 --max-line-length=$max_line_length --extend-ignore=$flake8_ignore --exclude=.venv,immich-client,scripts,jenkins_logs "$target_dir"
	fi
	if [ $? -ne 0 ]; then
		flake_failed=1
	fi
	if [ $flake_failed -ne 0 ]; then
		if [ "$quality_level" = "STRICT" ]; then
			echo "[ERROR] flake8 failed. See output above."
			return 1
		elif [ "$quality_level" = "STANDARD" ]; then
			echo "[ERROR] flake8 failed in STANDARD mode (all errors except E501). See output above."
			return 1
		elif [ "$quality_level" = "TARGET" ]; then
			echo "[ERROR] flake8 failed in TARGET mode (all errors except E501). See output above."
			return 1
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
			# STANDARD now blocks ALL mypy errors (mypy fully passes)
			echo "[STANDARD MODE] All mypy errors now block the build."
			return 1
		elif [ "$quality_level" = "TARGET" ]; then
			# TARGET now blocks ALL mypy errors (mypy fully passes)
			echo "[TARGET MODE] All mypy errors now block the build."
			return 1
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

	# Leer palabras desde fichero externo
	local SPANISH_WORDS_FILE="$SCRIPT_DIR/spanish_words.txt"
	local SPANISH_WORD_PATTERN=""
	if [[ -f "$SPANISH_WORDS_FILE" ]]; then
		# Filters empty lines or lines with only spaces
		SPANISH_WORD_PATTERN=$(grep -v '^#' "$SPANISH_WORDS_FILE" | grep -v '^[[:space:]]*$' | paste -sd '|' -)
	fi
	local SPANISH_PATTERN='[áéíóúñÁÉÍÓÚÑüÜ¿¡]'
	if [[ -n "$SPANISH_WORD_PATTERN" ]]; then
		SPANISH_PATTERN="$SPANISH_PATTERN|\\b($SPANISH_WORD_PATTERN)\\b"
	fi
	echo "[DEBUG] Generated regex pattern for Spanish: $SPANISH_PATTERN" >&2

	# Get relative paths for exclusion
	local SCRIPT_ABS_PATH QUALITY_GATE_ABS_PATH SCRIPT_REL_PATH QUALITY_GATE_REL_PATH
	SCRIPT_ABS_PATH="$(realpath "$0")"
	QUALITY_GATE_ABS_PATH="$(realpath "$BASH_SOURCE")"
	SCRIPT_REL_PATH="${SCRIPT_ABS_PATH#$PWD/}"
	QUALITY_GATE_REL_PATH="${QUALITY_GATE_ABS_PATH#$PWD/}"

	# Get git-tracked files and exclude this script, quality_gate.sh, and ONLY the spanish_words.txt file
	local files_to_check
	files_to_check=$(git ls-files | grep -v 'scripts/devtools/spanish_words.txt' | grep -v 'scripts/devtools/quality_gate_py/python_qualitygate/implementations/spanish_check/check_no_spanish_chars.py')

	# Search for Spanish characters/words in the selected files
	echo "[DEBUG] Files to check for Spanish:" >&2
	echo "$files_to_check" >&2
	spanish_matches=$(echo "$files_to_check" | xargs -r grep -n -I -i -P "$SPANISH_PATTERN" | grep -v '^.*SPANISH_PATTERN=.*$' || true)
	echo "[DEBUG] Results of Spanish grep:" >&2
	echo "$spanish_matches" >&2

	if [ -n "$spanish_matches" ]; then
		echo '❌ Spanish language characters detected in the following files/lines:'
		echo "$spanish_matches"
		# Count matches and affected files
		local match_count file_count
		match_count=$(echo "$spanish_matches" | grep -c '^')
		file_count=$(echo "$spanish_matches" | cut -d: -f1 | sort | uniq | wc -l)
		echo "Total matches: $match_count | Files affected: $file_count"
		quality_gate_status_message "[EXIT] Quality Gate failed due to forbidden Spanish characters.\n" \
			"Build failed: Please remove all Spanish text and accents before publishing.\n" \
			"Oops! Spanish detected. Let's keep it English, friends!"
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
	# Ensure import-linter is installed
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
	if ! "$lint_imports_bin" --config "$REPO_ROOT/importlinter.ini"; then
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
	# Defensive: Ensure local repo_root matches global REPO_ROOT
	if [ -n "$repo_root" ] && [ "$repo_root" != "$REPO_ROOT" ]; then
		echo "[DEFENSIVE-FAIL] repo_root argument ('$repo_root') does not match global REPO_ROOT ('$REPO_ROOT'). Exiting for safety." >&2
		return 99
	fi
	# All implemented check modules are called below. If a check is not called, it is either deprecated, not implemented, or not relevant for this mode. Add new checks here as needed.
	# 1. Blocking checks (fail fast on first error)
	check_python_syntax "$py_bin" "$target_dir" || return 1
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || return 1
	check_jscpd "$target_dir" || return 1
	check_import_linter "$REPO_ROOT" || return 1
	check_no_tuples "$py_bin" "$REPO_ROOT" "$target_dir" || return 3
	check_no_spanish_chars "$target_dir" || return 5
	# 2. Formatters and style (run only if all blocking checks pass)
	check_shfmt "$check_mode" "$target_dir" || return 1
	check_isort "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || return 1
	check_ssort "$check_mode" "$target_dir" || return 1
	check_black "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || return 1
	check_ruff "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" || return 1
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || return 1
	# 3. Dynamic attributes check (run last to ensure it doesn't block other checks from running)
	check_no_dynamic_attrs "$target_dir" "$quality_level" || return 2
}

# Run all quality checks in APPLY mode (run all, accumulate errors, fail at end)
run_quality_gate_apply_mode() {

	local py_bin="$1"
	local max_line_length="$2"
	local target_dir="$3"
	local quality_level="$4"
	local check_mode="$5"
	local repo_root="$6"
	local error_found=0

	# Defensive: Ensure local repo_root matches global REPO_ROOT
	if [ -n "$repo_root" ] && [ "$repo_root" != "$REPO_ROOT" ]; then
		echo "[DEFENSIVE-FAIL] repo_root argument ('$repo_root') does not match global REPO_ROOT ('$REPO_ROOT'). Exiting for safety." >&2
		return 99
	fi
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
	check_no_tuples "$py_bin" "$REPO_ROOT" "$target_dir" || error_found=3
	check_no_spanish_chars "$target_dir" || error_found=5
	# 4. Heavy/informative checks
	check_jscpd "$target_dir" || error_found=1
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || error_found=1
	check_import_linter "$REPO_ROOT" || error_found=1
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || error_found=1
	# 5. Dynamic attributes check (run last to ensure it doesn't block other checks from running)
	check_no_dynamic_attrs "$target_dir" "$quality_level" || error_found=2
	if [ "$error_found" -ne 0 ]; then
		quality_gate_status_message "[EXIT] Quality Gate failed (see errors above)."
		# After APPLY fails, run summary check in priority order (most important errors first)
		run_quality_gate_check_summary "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$repo_root"
		return $error_found
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

	# Defensive: Ensure local repo_root matches global REPO_ROOT
	if [ -n "$repo_root" ] && [ "$repo_root" != "$REPO_ROOT" ]; then
		echo "[DEFENSIVE-FAIL] repo_root argument ('$repo_root') does not match global REPO_ROOT ('$REPO_ROOT'). Exiting for safety." >&2
		return 99
	fi
	echo "[SUMMARY] Running prioritized checks to show the most important remaining error."
	# All implemented check modules are called below in priority order. If a check is not called, it is either deprecated, not implemented, or not relevant for this summary mode. Add new checks here as needed.
	# 1. Checks we have already passed (quality threshold):
	#    We put first the checks that we have already passed (like the language check),
	#    so that if they break, it is very obvious and immediately visible.
	#    This way we avoid quality deterioration in aspects that are already under control.
	check_no_spanish_chars "$target_dir" || return 5
	check_mypy "$check_mode" "$quality_level" "$py_bin" "$target_dir" || return 1
	# 2. Syntax errors
	check_python_syntax "$py_bin" "$target_dir" || return 1
	# 3. Ruff (lint/auto-fix)
	check_ruff "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" || return 1
	# 4. Flake8 (style)
	check_flake8 "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir" || return 1
	check_import_linter "$REPO_ROOT" || return 1
	# 5. Policy checks
	check_no_tuples "$py_bin" "$REPO_ROOT" "$target_dir" || return 3
	# 6. Code duplication (least urgent)
	check_jscpd "$target_dir" || return 1
	# 7. Formatters (least urgent in summary)
	check_shfmt "$check_mode" "$target_dir" || return 1
	# 8. Dynamic attributes check (run last to ensure it doesn't block other checks from running)
	check_no_dynamic_attrs "$target_dir" "$quality_level" || return 2
	check_isort "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || return 1
	check_ssort "$check_mode" "$target_dir" || return 1
	check_black "$check_mode" "$py_bin" "$max_line_length" "$target_dir" || return 1
}

# Refactor: main uses only local variables and passes values explicitly
main() {
	# Argument and global variable initialization
	local check_mode quality_level target_dir only_check max_line_length py_bin exit_code=0
	read -r check_mode quality_level target_dir only_check < <(parse_args_and_globals "$@")

	# Setup environment: max_line_length (safe, always returns a value)
	max_line_length=$(setup_max_line_length)

	# Setup environment: python_bin (must check for errors)
	py_bin=$(setup_python_venv_env)
	exit_code=$?
	if [ $exit_code -ne 0 ]; then
		echo "[SETUP-ERROR] Failed to initialize Python environment (exit code: $exit_code)." >&2
		quality_gate_print_reproduced_command
		return $exit_code
	fi

	# If --only-check is provided, run only that check and exit
	if [ -n "$only_check" ]; then
		if ! declare -f "$only_check" >/dev/null; then
			echo "[DEFENSIVE-FAIL] Unknown check function: $only_check" >&2
			quality_gate_print_reproduced_command
			return 90
		fi
		# Defensive: call with correct argument order for check_mypy and check_flake8
		set +e
		if [ "$only_check" = "check_mypy" ]; then
			"$only_check" "$check_mode" "$quality_level" "$py_bin" "$target_dir"
		elif [ "$only_check" = "check_flake8" ]; then
			"$only_check" "$check_mode" "$quality_level" "$py_bin" "$max_line_length" "$target_dir"
		else
			"$only_check" "$check_mode" "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$repo_root"
		fi
		exit_code=$?
		set -e
		if [ $exit_code -eq 0 ]; then
			quality_gate_status_message "[ONLY-CHECK] $only_check passed."
		else
			quality_gate_status_message "[ONLY-CHECK] $only_check failed."
		fi
		quality_gate_print_reproduced_command
		return $exit_code
	fi

	# Pass values explicitly to the check functions
	# All quality gate modules/checks are called via run_quality_gate_check_mode and run_quality_gate_apply_mode.
	# If a check is not called, it is either deprecated or not implemented yet. Add new checks to those functions.
	if [ "$check_mode" = "CHECK" ]; then
		run_quality_gate_check_mode "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$REPO_ROOT"
		exit_code=$?
	elif [ "$check_mode" = "APPLY" ]; then
		run_quality_gate_apply_mode "$py_bin" "$max_line_length" "$target_dir" "$quality_level" "$check_mode" "$REPO_ROOT"
		exit_code=$?
	else
		echo "[DEFENSIVE-FAIL] Unexpected check_mode value in main: '$check_mode'. Exiting for safety." >&2
		quality_gate_print_reproduced_command
		return 92
	fi

	# Print success or failure messages
	if [ $exit_code -eq 0 ]; then
		quality_gate_status_message "🎉 Quality Gate completed successfully!"
		quality_gate_status_message "All checks passed! Your code is cleaner than a robot's hard drive."
	else
		quality_gate_status_message "[EXIT] Quality Gate failed with exit code: $exit_code"
	fi

	# Always print the reproducible command at the end
	quality_gate_print_reproduced_command

	return $exit_code
}

# Entrypoint
main "$@"
