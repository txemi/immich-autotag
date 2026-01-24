#!/bin/bash

# loop_immich_autotag.sh
# Infinite loop to run immich-autotag with pipx every 5 minutes

SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"

while true; do
	echo "[$(date)] Running immich-autotag..."
	"$SCRIPT_DIR/run_immich_autotag.sh"
	echo "[$(date)] Waiting 5 minutes before the next execution..."
	sleep 300
done
