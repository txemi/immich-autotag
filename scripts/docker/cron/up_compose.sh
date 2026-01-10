
#!/bin/bash
# Robust script to start the autotag-cron service with Docker Compose from any directory
set -e

# Calculate script directory and repo root (two levels up from cron)
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$REPO_ROOT"

docker compose up -d

echo "autotag-cron service started with Docker Compose."
