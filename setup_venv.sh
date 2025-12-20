#!/bin/bash
# Script to create virtual environment, install dependencies, generate and install the local client
# Usage: source setup_venv.sh

set -e

VENV_DIR=".venv"
CLIENT_DIR="immich-client"
OPENAPI_URL="https://raw.githubusercontent.com/immich-app/immich/main/open-api/immich-openapi-specs.json"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Entorno virtual creado en $VENV_DIR"
else
    echo "El entorno virtual ya existe en $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Entorno virtual activado."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    # Instala solo dependencias que no sean el cliente local
    grep -v '^immich-client' requirements.txt | grep -v '^#' | xargs -r pip install
    echo "Dependencias instaladas."
else
    echo "requirements.txt not found."
fi

# Install the generator if not present
if ! pip show openapi-python-client > /dev/null 2>&1; then
    pip install openapi-python-client
    echo "openapi-python-client instalado."
fi

# Genera el cliente si no existe la carpeta
if [ ! -d "$CLIENT_DIR" ]; then
    openapi-python-client generate --url "$OPENAPI_URL"
    echo "Cliente immich-client generado."
else
    echo "The folder $CLIENT_DIR already exists. If you want to regenerate, delete it first."
fi

# Instala el cliente local si existe la carpeta
if [ -d "$CLIENT_DIR" ]; then
    pip install -e "$CLIENT_DIR"
    echo "Cliente local immich-client instalado."
else
    echo "The folder $CLIENT_DIR was not found."
fi
