
#!/bin/bash
# Robust script to create virtual environment, install dependencies, and generate/install the local client
# Automatically detects Immich server version and downloads the matching OpenAPI spec
# Always operates from the repository root, regardless of the invocation directory
# Usage: source setup_venv.sh

set -e

# Determine the repository root (where this script is located)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV_DIR="$REPO_ROOT/.venv"
CLIENT_DIR="$REPO_ROOT/immich-client"
CONFIG_FILE="$HOME/.config/immich_autotag/config.py"

# Function to extract config value from Python file
extract_config() {
    local key=$1
    local value=""
    
    if [ ! -f "$CONFIG_FILE" ]; then
        return
    fi
    
    # Use grep + sed to extract value
    # Handles both quoted strings: key="value" or key='value'
    # And unquoted values: key=123
    value=$(grep -E "^\s*$key\s*=" "$CONFIG_FILE" | sed -E 's/.*=\s*["\x27]?([^"\x27,]*)(["\x27,].*)?/\1/' | head -1 | tr -d '\n\r\t ')
    
    echo "$value"
}

# Function to get Immich server version from API
get_immich_version() {
    local host=$1
    local port=$2
    local api_key=$3
    
    if [ -z "$host" ] || [ -z "$port" ] || [ -z "$api_key" ]; then
        echo "main"
        return
    fi
    
    # Try to get server version from API endpoint /api/server/version
    # Returns JSON like: {"major": 2, "minor": 4, "patch": 1}
    local response=$(curl -s -m 5 -H "x-api-key: $api_key" \
        "http://$host:$port/api/server/version" 2>/dev/null)
    
    if [ -z "$response" ]; then
        echo "main"
        return
    fi
    
    # Extract version numbers using grep
    local major=$(echo "$response" | grep -o '"major":[0-9]*' | cut -d':' -f2)
    local minor=$(echo "$response" | grep -o '"minor":[0-9]*' | cut -d':' -f2)
    local patch=$(echo "$response" | grep -o '"patch":[0-9]*' | cut -d':' -f2)
    
    if [ -z "$major" ] || [ -z "$minor" ] || [ -z "$patch" ]; then
        echo "main"
    else
        # Format as v<major>.<minor>.<patch> (e.g., v2.4.1)
        echo "v${major}.${minor}.${patch}"
    fi
}

# Read Immich configuration
IMMICH_HOST=""
IMMICH_PORT=""
IMMICH_API_KEY=""

if [ -f "$CONFIG_FILE" ]; then
    echo "Reading configuration from $CONFIG_FILE..."
    IMMICH_HOST=$(extract_config "host")
    IMMICH_PORT=$(extract_config "port")
    IMMICH_API_KEY=$(extract_config "api_key")
fi

# Get server version and construct OpenAPI spec URL
if [ -n "$IMMICH_HOST" ] && [ -n "$IMMICH_PORT" ] && [ -n "$IMMICH_API_KEY" ]; then
    echo "Connecting to Immich at http://$IMMICH_HOST:$IMMICH_PORT to detect version..."
    IMMICH_VERSION=$(get_immich_version "$IMMICH_HOST" "$IMMICH_PORT" "$IMMICH_API_KEY")
    echo "Detected Immich version: $IMMICH_VERSION"
else
    echo "WARNING: Could not read Immich config. Config values: host='$IMMICH_HOST' port='$IMMICH_PORT' api_key_length=${#IMMICH_API_KEY}"
    echo "WARNING: Using default OpenAPI spec from 'main' branch."
    IMMICH_VERSION="main"
fi

# Construct the URL with the detected version
OPENAPI_URL="https://raw.githubusercontent.com/immich-app/immich/$IMMICH_VERSION/open-api/immich-openapi-specs.json"
echo "Using OpenAPI spec from: $OPENAPI_URL"



if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Virtual environment activated."

if [ -f "$REPO_ROOT/requirements.txt" ]; then
    pip install --upgrade pip
    # Install dependencies except the local client
    grep -v '^immich-client' "$REPO_ROOT/requirements.txt" | grep -v '^#' | xargs -r pip install
    echo "Dependencies installed."
else
    echo "requirements.txt not found."
fi


# Install the generator if not present
if ! pip show openapi-python-client > /dev/null 2>&1; then
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
