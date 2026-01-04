#!/bin/bash
# DISCLAIMER:
# This script is intended ONLY for quick, repeated updates of tags during heavy asset update sessions.
# It is NOT designed to run as a background service or daemon.
# Use it for rapid, manual update cycles when you need to refresh tags frequently.
# Between each execution, the script waits for 1 minute to avoid excessive load.
# Use with caution!

while true; do
    ./run_app.sh
    echo "Waiting 1 minute before next run..."
    sleep 60
done
