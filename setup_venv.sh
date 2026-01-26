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
	for arg in "$@"; do
		case $arg in
		--clean)
			CLEAN=1
			;;
		--prod)
			MODE="prod"
			;;
		--dev)
			MODE="dev"
			;;
		--help | -h)
			SHOW_HELP=1
			;;
		esac
	done
}

print_help() {
	echo "Usage: $0 [--clean] [--prod] [--dev] [--help]"
	echo "  --clean   Deletes .venv and immich-client before creating environment and client."
	echo "  --prod    Only installs runtime (production) dependencies."
	echo "  --dev     Installs development dependencies (default)."
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
	local response=$(curl -s -m 5 -H "x-api-key: $api_key" "$url" 2>&1)
	local curl_exit=$?
	echo "[DEBUG] curl exit code: $curl_exit" >&2
	echo "[DEBUG] API response: $response" >&2
	if [ $curl_exit -ne 0 ] || [ -z "$response" ]; then
		echo "[DEBUG] curl failed or empty response, returning 'main'" >&2
		echo "main"
		return
	fi
	local major=$(echo "$response" | grep -o '"major":[0-9]*' | cut -d':' -f2)
	local minor=$(echo "$response" | grep -o '"minor":[0-9]*' | cut -d':' -f2)
	local patch=$(echo "$response" | grep -o '"patch":[0-9]*' | cut -d':' -f2)
	echo "[DEBUG] Extracted: major='$major' minor='$minor' patch='$patch'" >&2
	if [ -z "$major" ] || [ -z "$minor" ] || [ -z "$patch" ]; then
		echo "[DEBUG] Failed to extract version numbers, returning 'main'" >&2
		echo "main"
	else
		local version="v${major}.${minor}.${patch}"
		echo "[DEBUG] Detected version: $version" >&2
		echo "$version"
	fi
}

# Gets the appropriate OpenAPI URL according to the configuration
get_openapi_url() {
	local config_file="$1"
	local default_version="v2.4.1"
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

	if [ -n "$immich_host" ] && [ -n "$immich_port" ] && [ -n "$immich_api_key" ]; then
		echo "Connecting to Immich at http://$immich_host:$immich_port to detect version..."
		immich_version=$(get_immich_version "$immich_host" "$immich_port" "$immich_api_key")
		echo "Detected Immich version: $immich_version"
	else
		echo "WARNING: Could not read Immich config. Config values: host='$immich_host' port='$immich_port' api_key_length=${#immich_api_key}"
		echo "WARNING: Using default OpenAPI spec version: $default_version"
		immich_version="$default_version"
	fi
	local openapi_url="https://raw.githubusercontent.com/immich-app/immich/$immich_version/open-api/immich-openapi-specs.json"
	echo "Using OpenAPI spec from: $openapi_url"
	# Export for use in main
	OPENAPI_URL="$openapi_url"
}
create_venv() {
	if [ ! -d "$VENV_DIR" ]; then
		python3 -m venv "$VENV_DIR"
		echo "Virtual environment created at $VENV_DIR"
	else
		echo "Virtual environment already exists at $VENV_DIR"
	fi
	source "$VENV_DIR/bin/activate"
	echo "Virtual environment activated."
}

# Instala dependencias Python de runtime
install_python_requirements() {
	if [ -f "$REPO_ROOT/requirements.txt" ]; then
		pip install --upgrade pip
		grep -v '^immich-client' "$REPO_ROOT/requirements.txt" | grep -v '^#' | xargs -r pip install
		echo "Runtime dependencies installed."
	else
		echo "requirements.txt not found."
	fi
}

# Instala herramientas de desarrollo del sistema (solo modo dev)
install_system_dev_tools() {
	if [ "$MODE" = "dev" ]; then
		# Solo Ubuntu/Debian
		if command -v apt-get >/dev/null 2>&1; then
			echo "[DEV] Installing system development tools (shfmt, etc.)..."
			sudo apt-get update
			sudo apt-get install -y shfmt
			# WARNING: Do not install Python or Node.js packages globally.
			# If jscpd is needed, install only via the distribution package manager (apt, dnf, etc) or in a local environment.
			# FORBIDDEN: Do not install Python or Node.js packages globally (no pip install --user, no npm install -g, no sudo pip/npm).
			# If jscpd is not in the repositories, document the need and look for a packaged alternative.
		else
			echo "[DEV] Skipping system tools installation: apt-get not found. Install shfmt and jscpd manually if needed."
		fi
	fi
}

# Instala dependencias Python de desarrollo (solo modo dev)
install_python_dev_requirements() {
	if [ "$MODE" = "dev" ]; then
		if [ -f "$REPO_ROOT/requirements-dev.txt" ]; then
			pip install -r "$REPO_ROOT/requirements-dev.txt"
			echo "Development dependencies installed."
		else
			echo "requirements-dev.txt not found. Skipping dev dependencies."
		fi
	else
		echo "Production mode: only runtime dependencies installed."
	fi
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

	# Generate the client only if the folder does not exist at the root
	if [ ! -d "$CLIENT_DIR" ]; then
		openapi-python-client generate --url "$OPENAPI_URL" --output-path "$CLIENT_DIR"
		echo "immich-client generated."
	else
		echo "The folder $CLIENT_DIR already exists. Regenerating..."
		rm -rf "$CLIENT_DIR" || true
		openapi-python-client generate --url "$OPENAPI_URL" --output-path "$CLIENT_DIR" --overwrite
		echo "immich-client regenerated."
	fi

	# Install the local client if the folder exists at the root
	if [ -d "$CLIENT_DIR" ]; then
		pip install -e "$CLIENT_DIR"
		echo "Local immich-client installed."
	else
		echo "The folder $CLIENT_DIR was not found."
		exit 1
	fi
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

	# Get the appropriate OpenAPI URL
	get_openapi_url "$CONFIG_FILE"

	create_venv
	install_dependencies
	generate_and_install_client
}

# --- EXECUTION ---
main "$@"
