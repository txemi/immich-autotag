#!/bin/bash
# stop_compose.sh
# Stops all running Docker Compose services for the project
# Usage: bash scripts/docker/stop_compose.sh
set -euo pipefail

# Detect project root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(realpath "$SCRIPT_DIR/../..")"
cd "$PROJECT_ROOT"

if [ ! -f docker/docker-compose.yml ]; then
  echo "[ERROR] docker-compose.yml not found in $PROJECT_ROOT/docker."
  exit 1
fi

echo "[INFO] Stopping all Docker Compose services for immich-autotag..."
docker compose -f docker/docker-compose.yml down

echo "[OK] All Docker Compose services stopped."
