#!/bin/bash
# DISCLAIMER:
# This script is intended ONLY for quick, repeated updates of tags during heavy asset update sessions.
# It is NOT designed to run as a background service or daemon.
# Use it for rapid, manual update cycles when you need to refresh tags frequently.
# Between each execution, the script waits for 1 minute to avoid excessive load.
# Use with caution!

# Detect repo root (two levels up from this script)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# If --setup is passed as an argument, run setup_venv.sh
RUN_SETUP=false
ARGS=()
for arg in "$@"; do
    if [ "$arg" == "--setup" ]; then
        RUN_SETUP=true
    else
        ARGS+=("$arg")
    fi
done

if [ "$RUN_SETUP" = true ]; then
    bash "$REPO_ROOT/setup_venv.sh"
fi

while bash "$REPO_ROOT/run_app.sh" "${ARGS[@]}" || true ; do
    echo "Waiting 1 minute before next run..."
    sleep 60
done
