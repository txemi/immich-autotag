#!/bin/bash
# loop_immich_autotag.sh
# Bucle infinito para ejecutar immich-autotag con pipx cada 5 minutos

while true; do
  echo "[$(date)] Ejecutando immich-autotag..."
  pipx run immich-autotag
  echo "[$(date)] Esperando 5 minutos antes de la siguiente ejecución..."
  sleep 300
done
