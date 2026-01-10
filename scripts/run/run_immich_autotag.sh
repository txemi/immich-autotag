#!/usr/bin/env bash
# Instala y ejecuta el CLI desde PyPI producción usando pipx

if ! command -v pipx &> /dev/null; then
  echo "[INFO] pipx no está instalado. Instalando..."
  pip install --user pipx
  export PATH="$HOME/.local/bin:$PATH"
fi

pipx run immich-autotag "$@"
