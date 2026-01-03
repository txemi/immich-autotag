#!/bin/bash
# Script to create virtual environment, install dependencies, generate and install the local client
# Usage: source setup_venv.sh

set -e

VENV_DIR=".venv"
CLIENT_DIR="immich-client"
OPENAPI_URL="https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Virtual environment activated."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    # Install only dependencies that are not the local client
    grep -v '^immich-client' requirements.txt | grep -v '^#' | xargs -r pip install
    echo "Dependencies installed."
else
    echo "requirements.txt not found."
fi

# Install the generator if not present
if ! pip show openapi-python-client > /dev/null 2>&1; then
    pip install openapi-python-client
    echo "openapi-python-client installed."
fi

# Generate the client if the folder does not exist
if [ ! -d "$CLIENT_DIR" ]; then
    openapi-python-client generate --url "$OPENAPI_URL"
    echo "immich-client generated."
else
    echo "The folder $CLIENT_DIR already exists. If you want to regenerate, delete it first."
fi

# Install the local client if the folder exists
if [ -d "$CLIENT_DIR" ]; then
    pip install -e "$CLIENT_DIR"
    echo "Local immich-client installed."
else
    echo "The folder $CLIENT_DIR was not found."
fi
