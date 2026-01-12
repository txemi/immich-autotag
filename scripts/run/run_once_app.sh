#!/bin/bash
# Script to run a single execution of Immich AutoTag with environment setup

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

bash "$REPO_ROOT/setup_venv.sh"
bash "$REPO_ROOT/run_app.sh" "$@"
