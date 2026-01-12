#!/bin/bash

# loop_immich_autotag.sh
# Infinite loop to run immich-autotag with pipx every 5 minutes

while true; do
  echo "[$(date)] Running immich-autotag..."
  pipx run immich-autotag
  echo "[$(date)] Waiting 5 minutes before the next execution..."
  sleep 300
done
