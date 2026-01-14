
#!/bin/bash
# Robust script to create virtual environment, install dependencies, and generate/install the local client
# Always operates from the repository root, regardless of the invocation directory
# Usage: source setup_venv.sh

set -e



# Determine the repository root (where this script is located)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

VENV_DIR="$REPO_ROOT/.venv"
CLIENT_DIR="$REPO_ROOT/immich-client"
OPENAPI_URL="https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"



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
