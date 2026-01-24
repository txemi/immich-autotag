#!/usr/bin/env bash
# Installs and runs the CLI from production PyPI using pipx

if ! command -v pipx &>/dev/null; then
	echo "[INFO] pipx is not installed. Attempting installation with apt..."
	if command -v apt &>/dev/null; then
		sudo apt update && sudo apt install -y pipx && export PATH="$HOME/.local/bin:$PATH"
	fi
fi

if ! command -v pipx &>/dev/null; then
	echo "[INFO] apt installation failed or not available. Trying pip installation..."
	pip install --user pipx && export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v pipx &>/dev/null; then
	echo "[ERROR] pipx could not be installed automatically. Please install pipx manually."
	exit 1
fi

pipx run immich-autotag "$@"
