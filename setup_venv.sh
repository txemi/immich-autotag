

#!/bin/bash
# Robust script to create virtual environment, install dependencies, and generate/install the local client
# Automatically detects Immich server version and downloads the matching OpenAPI spec
# Always operates from the repository root, regardless of the invocation directory

# Usage:
#   ./setup_venv.sh [--clean]
#   --clean   Deletes .venv and immich-client before creating environment and client

set -e

# --- MAIN FUNCTIONS ---


parse_args() {
	CLEAN=0
	SHOW_HELP=0
	MODE="dev" # Default mode
	CLI_IMMICH_VERSION=""

	while [ $# -gt 0 ]; do
		case "$1" in
		--clean)
			CLEAN=1
			shift
			;;
		--prod)
			MODE="prod"
			shift
			;;
		--dev)
			MODE="dev"
			shift
			;;
		--help|-h)
			SHOW_HELP=1
			shift
			;;
		--immich-version)
			CLI_IMMICH_VERSION="$2"
			shift 2
			;;
		--immich-version=*)
			CLI_IMMICH_VERSION="${1#*=}"
			shift
			;;
		*)
			shift
			;;
		esac
	done
}

print_help() {
	echo "Usage: $0 [--clean] [--prod] [--dev] [--help] [--immich-version <version>]"
	echo "  --clean   Deletes .venv and immich-client before creating environment and client."
	echo "  --prod    Only installs runtime (production) dependencies."
	echo "  --dev     Installs development dependencies (default)."
	echo "  --immich-version <vX.Y.Z>  Explicit Immich server version to use for immich-client generation."
	echo "  --help    Shows this help and exits."
}
# --- AUXILIARY FUNCTIONS ---

# Inicializa rutas y variables globales
init_paths() {
	REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	cd "$REPO_ROOT"

	VENV_DIR="$REPO_ROOT/.venv"
	CLIENT_DIR="$REPO_ROOT/immich-client"
	CONFIG_FILE="$HOME/.config/immich_autotag/config.py"
}

clean_env() {
	echo "Cleaning $VENV_DIR and $CLIENT_DIR..."
	rm -rf "$VENV_DIR" "$CLIENT_DIR"
	echo "Cleanup completed."
}

extract_config() {
	local key=$1
	local value=""
	if [ ! -f "$CONFIG_FILE" ]; then
		return
	fi
	value=$(grep -E "^\s*$key\s*=" "$CONFIG_FILE" | sed -E 's/.*=\s*["\x27]?([^"\x27,]*)(["\x27,].*)?/\1/' | head -1 | tr -d '\n\r\t ')
	echo "$value"
}

get_immich_version() {
	local host=$1
	local port=$2
	local api_key=$3
	echo "[DEBUG] get_immich_version called with:" >&2
	echo "  host='$host'" >&2
	echo "  port='$port'" >&2
	echo "  api_key_length=${#api_key}" >&2
	if [ -z "$host" ] || [ -z "$port" ] || [ -z "$api_key" ]; then
		echo "[DEBUG] Missing parameters, returning 'main'" >&2
		echo "main"
		return
	fi
	local url="http://$host:$port/api/server/version"
	echo "[DEBUG] Calling API: $url" >&2
	local response_raw
	response_raw=$(curl -sS --connect-timeout 5 -m 12 --retry 2 --retry-delay 1 --retry-connrefused -H "x-api-key: $api_key" -w "\n__HTTP_STATUS__:%{http_code}" "$url" 2>&1)
	local curl_exit=$?
	local http_status
	http_status=$(echo "$response_raw" | tail -n 1 | sed -E 's/^__HTTP_STATUS__://')
	local response
	response=$(echo "$response_raw" | sed '$d')
	echo "[DEBUG] curl exit code: $curl_exit" >&2
	echo "[DEBUG] HTTP status: ${http_status:-unknown}" >&2
	echo "[DEBUG] API response: $response" >&2
	if [ $curl_exit -ne 0 ] || [ -z "$response" ] || [ "${http_status:-0}" -ne 200 ]; then
		echo "[DEBUG] curl failed or empty response, returning 'main'" >&2
		echo "main"
		return
	fi

	# Try multiple parsing strategies for the version information.
	# 1) JSON fields: "major", "minor", "patch"
	local major
	local minor
	local patch
	major=$(echo "$response" | grep -o '"major"[[:space:]]*:[[:space:]]*[0-9]\+' | grep -o '[0-9]\+') || true
	minor=$(echo "$response" | grep -o '"minor"[[:space:]]*:[[:space:]]*[0-9]\+' | grep -o '[0-9]\+') || true
	patch=$(echo "$response" | grep -o '"patch"[[:space:]]*:[[:space:]]*[0-9]\+' | grep -o '[0-9]\+') || true
	if [ -n "$major" ] && [ -n "$minor" ] && [ -n "$patch" ]; then
		local version="v${major}.${minor}.${patch}"
		echo "[DEBUG] Detected version (major/minor/patch): $version" >&2
		echo "$version"
		return
	fi

	# 2) JSON field: "version": "vX.Y.Z" or "tag_name": "vX.Y.Z"
	local version_str
	version_str=$(echo "$response" | grep -o '"version"[[:space:]]*:[[:space:]]*"[vV]?[0-9]\+\.[0-9]\+\.[0-9]\+"' | sed -E 's/.*"([vV]?[0-9]+\.[0-9]+\.[0-9]+)".*/\1/') || true
	if [ -z "$version_str" ]; then
		version_str=$(echo "$response" | grep -o '"tag_name"[[:space:]]*:[[:space:]]*"[vV]?[0-9]\+\.[0-9]\+\.[0-9]\+"' | sed -E 's/.*"([vV]?[0-9]+\.[0-9]+\.[0-9]+)".*/\1/') || true
	fi
	if [ -n "$version_str" ]; then
		# normalize to leading 'v'
		version_str="${version_str#v}"
		echo "[DEBUG] Detected version (version field): v$version_str" >&2
		echo "v$version_str"
		return
	fi

	# 3) Fallback: find first semver-like tag anywhere in the response (e.g., v2.6.3)
	local semver
	semver=$(echo "$response" | grep -o -m 1 'v[0-9]\+\.[0-9]\+\.[0-9]\+' || true)
	if [ -n "$semver" ]; then
		echo "[DEBUG] Detected version (semver fallback): $semver" >&2
		echo "$semver"
		return
	fi

	echo "[DEBUG] Could not detect version from server response, returning 'main'" >&2
	echo "main"
}

# Gets the appropriate OpenAPI URL according to the configuration
get_openapi_url() {
	local config_file="$1"
	local immich_host=""
	local immich_port=""
	local immich_api_key=""
	local immich_version=""

	if [ -f "$config_file" ]; then
		echo "Reading configuration from $config_file..."
		immich_host=$(extract_config "host")
		immich_port=$(extract_config "port")
		immich_api_key=$(extract_config "api_key")
	fi

	# Priorities for determining immich_version (simple and explicit):
	# 1) CLI argument --immich-version (stored in CLI_IMMICH_VERSION)
	# 2) ENV var IMMICH_CLIENT_FALLBACK
	# 3) compatibility.yml (key: tested_immich)
	# 4) If real Immich config present (host/port/api_key) -> query server
	# 5) If running in Jenkins -> fail (coercive behavior retained)
	# 6) Otherwise -> error

	immich_version=""

	# 1) CLI argument
	if [ -n "${CLI_IMMICH_VERSION:-}" ]; then
		immich_version="$CLI_IMMICH_VERSION"
		echo "Using CLI immich version: $immich_version"
	fi

	# 2) ENV fallback (removed): prefer explicit CLI arg or compatibility.yml
	# Note: IMMICH_CLIENT_FALLBACK support was removed to keep a single
	# explicit source of truth (CLI arg or compatibility.yml). If you need
	# an override in CI, pass --immich-version or set compatibility.yml.

	# 3) compatibility.yml support removed: prefer explicit CLI arg or real server
	# Note: To keep the script simple and explicit, the compatibility.yml
	# automatic read was removed. Callers should pass --immich-version or
	# ensure server access (host/port/api_key) so the script can query the server.

	# 4) If we have concrete server config, query it
	if [ -z "$immich_version" ] && [ -n "$immich_host" ] && [ -n "$immich_port" ] && [ -n "$immich_api_key" ]; then
		echo "Connecting to Immich at http://$immich_host:$immich_port to detect version..."
		immich_version=$(get_immich_version "$immich_host" "$immich_port" "$immich_api_key")
		echo "Detected Immich version: $immich_version"
		if [ "$immich_version" = "main" ]; then
			echo "ERROR: Failed to detect concrete Immich server version (detected 'main')." >&2
			echo "ERROR: Refusing to generate immich-client from 'main' because this can produce an incompatible version." >&2
			echo "ERROR: Verify network access to /api/server/version and API key validity." >&2
			exit 1
		fi
	fi

	# 5) Jenkins: be strict and fail if no version determined
	IS_JENKINS=false
	if [ -n "${JENKINS_URL:-}" ] || [ -n "${JENKINS_HOME:-}" ]; then
		IS_JENKINS=true
	fi
	if [ "${IS_JENKINS}" = "true" ] && [ -z "$immich_version" ]; then
		echo "Running in Jenkins and no Immich server/config detected: failing as configured." >&2
		exit 1
	fi

	# 6) final error if still empty
	if [ -z "$immich_version" ]; then
		echo "ERROR: Could not determine Immich version (no CLI arg, env, compatibility.yml, or server available)." >&2
		echo "ERROR: Config values: host='$immich_host' port='$immich_port' api_key_length=${#immich_api_key}" >&2
		exit 1
	fi

	local openapi_url="https://raw.githubusercontent.com/immich-app/immich/$immich_version/open-api/immich-openapi-specs.json"
	echo "Using OpenAPI spec from: $openapi_url"
	# Export for use in main
	OPENAPI_URL="$openapi_url"
}
create_venv() {
	if [ -d "$VENV_DIR" ]; then
		echo "Virtual environment already exists at $VENV_DIR"
		source "$VENV_DIR/bin/activate"
		echo "Virtual environment activated."
		return
	fi
	python3 -m venv "$VENV_DIR"
	echo "Virtual environment created at $VENV_DIR"
	source "$VENV_DIR/bin/activate"
	echo "Virtual environment activated."
}

# Instala dependencias Python de runtime
install_python_requirements() {
	if [ ! -f "$REPO_ROOT/requirements.txt" ]; then
		echo "requirements.txt not found."
		return
	fi
	pip install --upgrade pip
	grep -v '^immich-client' "$REPO_ROOT/requirements.txt" | grep -v '^#' | xargs -r pip install
	echo "Runtime dependencies installed."
}
# Install Node.js and npm if not present (for jscpd/quality gate)
install_nodejs_npm() {
	if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
		echo "[DEV] Node.js and npm already installed. Skipping."
		return
	fi
	if ! command -v apt-get >/dev/null 2>&1; then
		echo "[DEV] Skipping Node.js/npm installation: apt-get not found. Install nodejs and npm manually if needed."
		return
	fi
	echo "[DEV] Installing Node.js and npm (for jscpd/quality gate)..."
	if command -v sudo >/dev/null 2>&1; then
		sudo apt-get update && sudo apt-get install -y nodejs npm
	elif [ "$(id -u)" -eq 0 ]; then
		apt-get update && apt-get install -y nodejs npm
	else
		echo "ERROR: Neither sudo is available nor running as root. Cannot install nodejs/npm." >&2
		exit 1
	fi
	if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
		echo "ERROR: Node.js/npm installation failed. Please install them manually." >&2
		exit 1
	fi
}

# Install shfmt if not present
install_shfmt() {
	if command -v shfmt >/dev/null 2>&1; then
		echo "[DEV] shfmt already installed. Skipping system tools installation."
		return
	fi
	if ! command -v apt-get >/dev/null 2>&1; then
		echo "[DEV] Skipping system tools installation: apt-get not found. Install shfmt and jscpd manually if needed."
		return
	fi
	echo "[DEV] Installing system development tools (shfmt, etc.)..."
	if command -v sudo >/dev/null 2>&1; then
		sudo apt-get update && sudo apt-get install -y shfmt
	elif [ "$(id -u)" -eq 0 ]; then
		apt-get update && apt-get install -y shfmt
	else
		echo "ERROR: Neither sudo is available nor running as root. Cannot install shfmt." >&2
		exit 1
	fi
	if ! command -v shfmt >/dev/null 2>&1; then
		echo "ERROR: shfmt installation failed. Please install it manually." >&2
		exit 1
	fi
}
# Install curl if not present
install_curl() {
	if command -v curl >/dev/null 2>&1; then
		echo "[DEV] curl already installed. Skipping."
		return
	fi
	if ! command -v apt-get >/dev/null 2>&1; then
		echo "[DEV] Skipping curl installation: apt-get not found. Install curl manually if needed."
		return
	fi
	echo "[DEV] Installing curl..."
	if command -v sudo >/dev/null 2>&1; then
		sudo apt-get update && sudo apt-get install -y curl
	elif [ "$(id -u)" -eq 0 ]; then
		apt-get update && apt-get install -y curl
	else
		echo "ERROR: Neither sudo is available nor running as root. Cannot install curl." >&2
		exit 1
	fi
	if ! command -v curl >/dev/null 2>&1; then
		echo "ERROR: curl installation failed. Please install it manually." >&2
		exit 1
	fi
}
# Install gh CLI if not present
install_gh_cli() {
	if command -v gh >/dev/null 2>&1; then
		echo "[DEV] gh CLI already installed. Skipping."
		return
	fi
	if ! command -v apt-get >/dev/null 2>&1; then
		echo "[DEV] Skipping gh CLI installation: apt-get not found. Install gh manually if needed."
		return
	fi
	echo "[DEV] Installing GitHub CLI (gh)..."
	install_curl
	# Add GitHub CLI repo if not present
	if ! apt-cache policy | grep -q 'cli.github.com'; then
		if command -v sudo >/dev/null 2>&1; then
			curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
			sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
			echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
			sudo apt-get update
			sudo apt-get install -y gh
		elif [ "$(id -u)" -eq 0 ]; then
			curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
			chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
			echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
			apt-get update
			apt-get install -y gh
		else
			echo "ERROR: Neither sudo is available nor running as root. Cannot install gh CLI." >&2
			exit 1
		fi
	else
		if command -v sudo >/dev/null 2>&1; then
			sudo apt-get update && sudo apt-get install -y gh
		elif [ "$(id -u)" -eq 0 ]; then
			apt-get update && apt-get install -y gh
		else
			echo "ERROR: Neither sudo is available nor running as root. Cannot install gh CLI." >&2
			exit 1
		fi
	fi
	if ! command -v gh >/dev/null 2>&1; then
		echo "ERROR: gh CLI installation failed. Please install it manually." >&2
		exit 1
	fi
}
# Install system development tools (dev mode only)
install_system_dev_tools() {
	if [ "$MODE" = "dev" ]; then
		install_nodejs_npm
		install_shfmt
		install_gh_cli
	fi
}

# Install Python development dependencies (dev mode only)
install_python_dev_requirements() {
	if [ "$MODE" != "dev" ]; then
		echo "Production mode: only runtime dependencies installed."
		return
	fi
	if [ ! -f "$REPO_ROOT/requirements-dev.txt" ]; then
		echo "requirements-dev.txt not found. Skipping dev dependencies."
		return
	fi
	pip install -r "$REPO_ROOT/requirements-dev.txt"
	echo "Development dependencies installed."
}

# Orchestrates dependency installation
install_dependencies() {
	install_python_requirements
	install_system_dev_tools
	install_python_dev_requirements
}

generate_and_install_client() {
	# Install the generator if not present
	if ! pip show openapi-python-client >/dev/null 2>&1; then
		pip install openapi-python-client
		echo "openapi-python-client installed."
	fi

	if [ -d "$CLIENT_DIR" ]; then
		echo "The folder $CLIENT_DIR already exists. Regenerating..."
		rm -rf "$CLIENT_DIR" || true
		openapi-python-client generate --url "$OPENAPI_URL" --output-path "$CLIENT_DIR" --overwrite
		echo "immich-client regenerated."
	else
		openapi-python-client generate --url "$OPENAPI_URL" --output-path "$CLIENT_DIR"
		echo "immich-client generated."
	fi

	if [ ! -d "$CLIENT_DIR" ]; then
		echo "The folder $CLIENT_DIR was not found."
		exit 1
	fi
	pip install -e "$CLIENT_DIR"
	echo "Local immich-client installed."
}

# --- MAIN ---
main() {
	parse_args "$@"

	if [ "$SHOW_HELP" = "1" ]; then
		print_help
		exit 0
	fi

	init_paths

	if [ "$CLEAN" = "1" ]; then
		clean_env
	fi

	# Ensure curl is present before server-version detection.
	# In minimal CI images (e.g., python:slim), detection runs before dev tool install.
	install_curl

	# Get the appropriate OpenAPI URL
	get_openapi_url "$CONFIG_FILE"

	create_venv
	install_dependencies
	generate_and_install_client
}

# --- EXECUTION ---
main "$@"
