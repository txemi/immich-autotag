#!/bin/bash

# ============================================================================
# QUALITY GATE SCRIPT: CHECKS AND EXECUTION MODES
# ============================================================================
#
# Usage:
#   ./quality_gate.sh [--check|-c] [--strict] [--dummy] [target_dir]
#
# Modes:
#   --dummy   Dummy mode (default). Does nothing and always succeeds.
#   --strict  Enforce all checks strictly, fail on any error.
#   --check   Only check, do not modify files (default is apply/fix mode).
#   --relaxed Some non-critical checks are warnings only.
#   --enforce-dynamic-attrs  Enforce ban on getattr/hasattr (advanced).
#
# If no [target_dir] is given, defaults to the main package.
#
# =====================
# Quality Gate Checks Table (reference)
# =====================
# | Check                            | Description                                 | Strict   | Relaxed (CI) | Dummy |
# |-----------------------------------|---------------------------------------------|----------|--------------|-------|
# | Syntax/Indent (compileall)        | Python syntax errors                        |   ✔️     |   ✔️         |       |
# | ruff (lint/auto-fix)              | Linter and auto-format                      |   ✔️     |   ✔️         |       |
# | isort (import sorting)            | Sorts imports                               |   ✔️     |   ✔️         |       |
# | black (formatter)                 | Code formatter                              |   ✔️     |   ✔️         |       |
# | flake8 (style)                    | Style linter                                |   ✔️     |   ✔️         |       |
# | mypy (type check)                 | Type checking                               |   ✔️     |   ✔️         |       |
# | uvx ssort (method order)          | Class method ordering                       |   ✔️**   |   ✔️**       |       |
# | tuple return/type policy          | Forbids tuples as return/attribute          |   ✔️     |   ✔️         |       |
# | jscpd (code duplication)          | Detects code duplication                    |   ✔️     |   ✔️         |       |
# | Spanish character check           | Forbids Spanish text/accents                |   ✔️     |   Warn       |       |
# -----------------------------------------------------------------------------
# * In relaxed mode, flake8 ignores E501, and flake8 only warns, does not block the build.
# ** Only if --enforce-dynamic-attrs is used
#
# Developer Notes:
# - To harden the quality gate, consider adding security/static analysis tools (bandit, shellcheck), and enforcing coverage thresholds.
# - Update the table above if you add or change checks.

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
# Description: Interpreta argumentos de línea de comandos y define variables globales.
# Globals set: QUALITY_LEVEL, CHECK_MODE, ENFORCE_DYNAMIC_ATTRS, TARGET_DIR
# Usage: parse_args_and_globals "$@"
# Returns: Exporta variables globales y puede terminar el script en modo ayuda o dummy
###############################################################################
parse_args_and_globals() {
	if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
		echo "Usage: $0 [--check|-c] [--strict] [--dummy] [target_dir]"
		echo "Runs ruff/isort/black/flake8/mypy against the codebase. Uses .venv if present; otherwise falls back to system python."
		echo "  --dummy: Dummy mode (default). Does nothing and always succeeds."
		echo "  --strict: Enforce all checks strictly, fail on any error."
		exit 0
	fi


	# Definir como globales

	CHECK_MODE="APPLY"  # Valores posibles: APPLY, CHECK, DUMMY
	QUALITY_LEVEL=""  # Valores posibles: DUMMY, STRICT, RELAXED
	ENFORCE_DYNAMIC_ATTRS=0
	TARGET_DIR=""
	for arg in "$@"; do
		if [ "$arg" = "--strict" ]; then
			QUALITY_LEVEL="STRICT"
		elif [ "$arg" = "--relaxed" ]; then
			QUALITY_LEVEL="RELAXED"
		elif [ "$arg" = "--dummy" ]; then
			CHECK_MODE="DUMMY"
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
	# Si el usuario no ha forzado QUALITY_LEVEL, lo inferimos de CHECK_MODE
	if [ -z "$QUALITY_LEVEL" ]; then
		if [ "$CHECK_MODE" = "APPLY" ]; then
			QUALITY_LEVEL="STRICT"
		elif [ "$CHECK_MODE" = "CHECK" ]; then
			QUALITY_LEVEL="RELAXED"
		elif [ "$CHECK_MODE" = "DUMMY" ]; then
			QUALITY_LEVEL="DUMMY"
		fi
	fi
	# If no positional argument was given, default to PACKAGE_NAME
	if [ -z "$TARGET_DIR" ]; then
		TARGET_DIR="$PACKAGE_NAME"
	fi

	export QUALITY_LEVEL CHECK_MODE ENFORCE_DYNAMIC_ATTRS TARGET_DIR

	if [ "$CHECK_MODE" = "DUMMY" ] || [ "$QUALITY_LEVEL" = "DUMMY" ]; then
		echo "[CHECK_MODE] Running in DUMMY mode (no checks will be performed, always succeeds)."
		exit 0
	elif [ "$QUALITY_LEVEL" = "STRICT" ]; then
		echo "[QUALITY_LEVEL] Running in STRICT mode (all checks enforced, fail on any error)."
	elif [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		echo "[QUALITY_LEVEL] Running in RELAXED mode (some checks are warnings only)."
	fi

	if [ "$CHECK_MODE" = "CHECK" ]; then
		echo "[CHECK_MODE] Running in CHECK mode (no files will be modified)."
	elif [ "$CHECK_MODE" = "APPLY" ]; then
		echo "[CHECK_MODE] Running in APPLY mode (formatters may modify files)."
	fi
}



###############################################################################
# Function: check_shfmt
# Description: Verifica y formatea scripts Bash usando shfmt.
# Globals: CHECK_MODE
# Returns: 0 si pasa, 1 si hay errores de formato o falta shfmt
###############################################################################
check_shfmt() {
	echo ""
	echo "==============================="
	echo "SECTION 1: BASH SCRIPT FORMATTING CHECK (shfmt)"
	echo "==============================="
	echo ""

	# Require shfmt to be installed
	if ! command -v shfmt >/dev/null 2>&1; then
		echo "[ERROR] shfmt is not installed. Please install it to pass the quality gate."
		echo "You can install it with: sudo apt-get install shfmt  # or equivalent for your system"
		return 1
	fi

	# Find relevant bash scripts (adjust pattern if needed)
	BASH_SCRIPTS=$(find scripts -type f -name "*.sh")

	# Run shfmt according to mode
	if [ "$CHECK_MODE" = "CHECK" ]; then
		if ! shfmt -d $BASH_SCRIPTS; then
			echo "[ERROR] There are formatting issues in Bash scripts. Run 'shfmt -w scripts/' to fix them."
			return 1
		fi
	else
		echo "[INFO] Applying automatic formatting to Bash scripts with shfmt..."
		shfmt -w $BASH_SCRIPTS
	fi
	return 0
}

# Call the first check

# =============================================================================
# SECTION A: SYNCHRONIZED CONFIGURATION EXTRACTION
# -----------------------------------------------------------------------------
# - Extracts line length and config values from pyproject.toml for all tools.  #
# =============================================================================

# =============================================================================
# Function: setup_max_line_length
# Description: Extrae el valor de line-length de pyproject.toml y lo exporta como MAX_LINE_LENGTH.
# Globals set: MAX_LINE_LENGTH
# =============================================================================
setup_max_line_length() {
	extract_line_length() {
		grep -E '^[ \t]*line-length[ \t]*=' "$1" | head -n1 | sed -E 's/.*= *([0-9]+).*/\1/'
	}
	MAX_LINE_LENGTH=$(extract_line_length "$REPO_ROOT/pyproject.toml")
	if [ -z "$MAX_LINE_LENGTH" ]; then
		echo "[WARN] Could not extract line-length from pyproject.toml, using 88 by default."
		MAX_LINE_LENGTH=88
	fi
	export MAX_LINE_LENGTH
}






# =============================================================================
# Function: setup_python_env
# Description: Activa el entorno virtual del proyecto o usa el Python del sistema.
# Globals set: PY_BIN
# Returns: nada, pero exporta PY_BIN o termina el script si no hay Python disponible
# =============================================================================
setup_python_env() {
	VENV_ACTIVATE="$REPO_ROOT/.venv/bin/activate"
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
# Description: Compila los archivos Python para detectar errores de sintaxis.
# Globals: PY_BIN, TARGET_DIR
# Returns: 0 si pasa, 1 si hay errores de sintaxis
###############################################################################
check_python_syntax() {
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
# Description: Instala una herramienta de Python en el entorno actual si falta.
# Globals: PY_BIN
# Usage: ensure_tool <import_name> <package_name>
# Returns: nada, pero instala el paquete si es necesario
###############################################################################
ensure_tool() {
	tool_import_check="$1"
	tool_pkg="$2"
	if ! "$PY_BIN" -c "import ${tool_import_check}" 2>/dev/null; then
		echo "Installing ${tool_pkg} into environment ($PY_BIN)..."
		"$PY_BIN" -m pip install "${tool_pkg}"
	fi
}


###############################################################################
# Function: check_isort
# Description: Ordena los imports de Python usando isort.
# Globals: CHECK_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 si pasa, 1 si hay problemas de ordenado
###############################################################################
check_isort() {
	ensure_tool isort isort
	ISORT_SKIPS="--skip .venv --skip immich-client --skip scripts --skip jenkins_logs --line-length $MAX_LINE_LENGTH"
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m isort $ISORT_SKIPS --profile black --check-only "$TARGET_DIR"
		ISORT_EXIT=$?
	else
		"$PY_BIN" -m isort $ISORT_SKIPS --profile black "$TARGET_DIR"
		ISORT_EXIT=$?
	fi
	if [ $ISORT_EXIT -ne 0 ]; then
		echo "[WARNING] isort reported issues."
		if [ "$CHECK_MODE" -eq 1 ]; then
			echo "Run in apply mode to let the script attempt to fix formatting problems or run the command locally to see the diffs."
			return 1
		fi
	fi
	return 0
}


# =============================================================================
# SECTION 9B: SSORT (DETERMINISTIC METHOD ORDERING)
# -----------------------------------------------------------------------------
# - ssort: Ensures deterministic method ordering in Python classes.
# =============================================================================
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



###############################################################################
# Function: ensure_ssort
# Description: Instala ssort desde GitHub si no está disponible en el entorno.
# Globals: PY_BIN
# Returns: nada, pero instala ssort si es necesario
###############################################################################
ensure_ssort() {
	if ! command -v ssort &>/dev/null; then
		echo "[INFO] ssort not found, installing from GitHub..."
		"$PY_BIN" -m pip install git+https://github.com/bwhmather/ssort.git
	fi
}


###############################################################################
# Function: check_ssort
# Description: Ordena métodos de clases Python de forma determinista usando ssort.
# Globals: CHECK_MODE, TARGET_DIR
# Returns: 0 si pasa, 1 si hay métodos desordenados
###############################################################################
check_ssort() {
	ensure_ssort
	SSORT_FAILED=0
	if [ "$CHECK_MODE" -eq 1 ]; then
		echo "[FORMAT] Running ssort in CHECK mode..."
		ssort --check "$TARGET_DIR" || SSORT_FAILED=1
	else
		echo "[FORMAT] Running ssort in APPLY mode..."
		ssort "$TARGET_DIR" || SSORT_FAILED=1
	fi
	if [ $SSORT_FAILED -ne 0 ]; then
		echo "[ERROR] ssort detected unsorted methods. Run in apply mode to fix."
		echo "[EXIT] Quality Gate failed due to ssort ordering errors."
		return 1
	fi
	return 0
}




###############################################################################
# Function: check_ruff
# Description: Lint y auto-fix de estilo Python usando ruff.
# Globals: CHECK_MODE, RELAXED_MODE, PY_BIN, TARGET_DIR
# Returns: 0 si pasa, 1 si hay problemas de estilo
###############################################################################
check_ruff() {
	ensure_tool ruff ruff
	RUFF_IGNORE=""
	if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		RUFF_IGNORE="--ignore E501"
		echo "[RELAXED MODE] Ruff will ignore E501 (line length) and will NOT block the build for it."
	fi
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m ruff check --fix $RUFF_IGNORE "$TARGET_DIR"
		RUFF_EXIT=$?
	else
		"$PY_BIN" -m ruff check --fix $RUFF_IGNORE "$TARGET_DIR"
		RUFF_EXIT=$?
	fi
	if [ $RUFF_EXIT -ne 0 ]; then
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
# Description: Formatea código Python usando Black.
# Globals: CHECK_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 si pasa, 1 si hay problemas de formato
###############################################################################
check_black() {
	# Format code with Black using the environment Python
	ensure_tool black black
	BLACK_EXCLUDES="--exclude .venv --exclude immich-client --exclude scripts --exclude jenkins_logs --line-length $MAX_LINE_LENGTH"
	if [ "$CHECK_MODE" = "CHECK" ]; then
		"$PY_BIN" -m black --check $BLACK_EXCLUDES "$TARGET_DIR"
		BLACK_EXIT=$?
	else
		"$PY_BIN" -m black $BLACK_EXCLUDES "$TARGET_DIR"
		BLACK_EXIT=$?
	fi
	if [ $BLACK_EXIT -ne 0 ]; then
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
# Description: Prohíbe el uso de getattr/hasattr para seguridad de tipado estático.
# Globals: ENFORCE_DYNAMIC_ATTRS, TARGET_DIR
# Returns: 0 si pasa, 1 si se detectan usos prohibidos
###############################################################################
check_no_dynamic_attrs() {
	# Policy enforcement: disallow dynamic attribute access via getattr() and hasattr()
	# Projects following our coding guidelines avoid these calls because they
	# undermine static typing and hide missing attributes. This check is strict
	# and is DISABLED by default (enabled only with --enforce-dynamic-attrs).
	if [ "$ENFORCE_DYNAMIC_ATTRS" -eq 1 ]; then
		if grep -R --line-number --exclude-dir=".venv" --exclude-dir="immich-client" --exclude-dir="scripts" --include="*.py" -E "getattr\(|hasattr\(" "$TARGET_DIR"; then
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
# Description: Prohíbe el uso de tuplas como retorno o atributos de clase.
# Globals: PY_BIN, REPO_ROOT, TARGET_DIR
# Returns: 0 si pasa, 1 si se detectan tuplas prohibidas
###############################################################################
check_no_tuples() {
	echo "[CHECK] Disallow tuple returns and tuple-typed class members (project policy)"
	"$PY_BIN" "${REPO_ROOT}/scripts/devtools/check_no_tuples.py" "$TARGET_DIR" --exclude ".venv,immich-client,scripts" || {
		echo "[ERROR] Tuple usage policy violations detected. Replace tuples with typed classes/dataclasses."
		return 1
	}
	return 0
}


###############################################################################
# Function: check_jscpd
# Description: Detecta duplicación de código usando jscpd.
# Globals: TARGET_DIR
# Returns: 0 si pasa, 1 si hay duplicación
###############################################################################
check_jscpd() {
	echo "[CHECK] Running jscpd for code duplication detection..."
	if ! command -v jscpd &>/dev/null; then
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
		return 1
	fi
	echo "jscpd check passed: no significant code duplication detected."
	return 0
}




###############################################################################
# Function: check_flake8
# Description: Lint de estilo y errores Python usando flake8.
# Globals: RELAXED_MODE, PY_BIN, MAX_LINE_LENGTH, TARGET_DIR
# Returns: 0 si pasa, 1 si hay errores de estilo
###############################################################################
check_flake8() {
	ensure_tool flake8 flake8
	FLAKE_FAILED=0
	FLAKE8_IGNORE="E203,W503"
	if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
		FLAKE8_IGNORE="$FLAKE8_IGNORE,E501"
		echo "[RELAXED MODE] E501 (line length) errors are ignored and will NOT block the build."
	fi
	echo "[INFO] Running flake8 (output below if any):"
	"$PY_BIN" -m flake8 --max-line-length=$MAX_LINE_LENGTH --extend-ignore=$FLAKE8_IGNORE --exclude=.venv,immich-client,scripts,jenkins_logs "$TARGET_DIR"
	if [ $? -ne 0 ]; then
		FLAKE_FAILED=1
	fi
	if [ $FLAKE_FAILED -ne 0 ]; then
		if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
			echo "[WARNING] flake8 failed, but relaxed mode is enabled. See output above."
			echo "[RELAXED MODE] Not blocking build on flake8 errors."
		else
			echo "[ERROR] flake8 failed. See output above."
			return 1
		fi
	fi
	return 0
}



###############################################################################
# Function: check_mypy
# Description: Chequeo de tipos estáticos usando mypy.
# Globals: PY_BIN, TARGET_DIR
# Returns: 0 si pasa, 1 si hay errores de tipado
###############################################################################
check_mypy() {
	ensure_tool mypy mypy
	MYPY_FAILED=0
	echo "[INFO] Running mypy (output below if any):"
	set +e
	MYPY_OUTPUT=$($PY_BIN -m mypy --ignore-missing-imports "$TARGET_DIR" 2>&1)
	MYPY_EXIT_CODE=$?
	set -e
	if [ $MYPY_EXIT_CODE -ne 0 ]; then
		MYPY_FAILED=1
	fi
	if [ $MYPY_FAILED -ne 0 ]; then
		echo "$MYPY_OUTPUT"
		# Count errors: lines containing 'error:'
		MYPY_ERROR_COUNT=$(echo "$MYPY_OUTPUT" | grep -c 'error:')
		MYPY_FILES_COUNT=$(echo "$MYPY_OUTPUT" | grep -o '^[^:]*:' | cut -d: -f1 | sort | uniq | wc -l)
		echo "[ERROR] MYPY FAILED. TOTAL ERRORS: $MYPY_ERROR_COUNT IN $MYPY_FILES_COUNT FILES."
		echo "[INFO] Command executed: $PY_BIN -m mypy --ignore-missing-imports $TARGET_DIR"
		echo "[EXIT] Quality Gate failed due to mypy errors."
		return 1
	fi
	echo "Static checks (ruff/flake8/mypy) completed successfully."
	return 0
}


###############################################################################
# Function: check_no_spanish_chars
# Description: Prohíbe caracteres españoles/acento en el código fuente.
# Globals: RELAXED_MODE
# Returns: 0 si pasa, 1 si se detectan caracteres prohibidos
###############################################################################
check_no_spanish_chars() {
	echo "Checking for Spanish language characters in source files..."
	SPANISH_MATCHES=$(grep -r -n -I -E '[áéíóúÁÉÍÓÚñÑüÜ¿¡]' . --exclude-dir={.git,.venv,node_modules,dist,build,logs_local,jenkins_logs} || true)
	if [ -n "$SPANISH_MATCHES" ]; then
		echo '❌ Spanish language characters detected in the following files/lines:'
		echo "$SPANISH_MATCHES"
		echo '[EXIT] Quality Gate failed due to forbidden Spanish characters.'
		if [ "$QUALITY_LEVEL" = "RELAXED" ]; then
			echo '[RELAXED MODE] Not blocking build on Spanish character check.'
		else
			echo 'Build failed: Please remove all Spanish text and accents before publishing.'
			return 1
		fi
	else
		echo "✅ No Spanish language characters detected."
	fi
	return 0
}






# =============================================================================
# Function: setup_environment
# Description: Inicializa entorno Python y longitud de línea máxima.
# Llama a setup_max_line_length y setup_python_env.
# =============================================================================
setup_environment() {
	setup_max_line_length
	setup_python_env
}

main() {
	# Inicialización de argumentos y variables globales
	parse_args_and_globals "$@"
	setup_environment
	check_shfmt || exit 1
	check_python_syntax || exit 1
	check_isort || exit 1
	check_ruff || exit 1
	check_black || exit 1
	check_ssort || exit 1
	check_no_dynamic_attrs || exit 2
	check_no_tuples || exit 3
	check_jscpd || exit 1
	check_flake8 || exit 1
	check_mypy || exit 1
	check_no_spanish_chars || exit 5

	echo "🎉 Quality Gate completed successfully!"
}



# Entrypoint
main "$@"
