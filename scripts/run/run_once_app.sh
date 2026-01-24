#!/bin/bash
# Script to run a single execution of Immich AutoTag, with optional environment setup
#
# NOTE: The setup step (setup_venv.sh) is optional because updating the client (immich-client)
# with the latest openapi-python-client sometimes breaks compatibility with the rest of the project.
# This allows you to use older, working versions of the client by default, and only update/setup
# when explicitly requested with --setup. This avoids unexpected failures due to breaking changes
# in the generated client code or dependencies.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
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

bash "$REPO_ROOT/run_app.sh" "${ARGS[@]}"
