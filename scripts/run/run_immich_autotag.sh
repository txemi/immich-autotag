#!/usr/bin/env bash
# Installs and runs the CLI from production PyPI using pipx

if ! command -v pipx &> /dev/null; then
  echo "[INFO] pipx is not installed. Installing..."
  pip install --user pipx
  export PATH="$HOME/.local/bin:$PATH"
fi

pipx run immich-autotag "$@"
