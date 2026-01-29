#!/bin/bash
# Activates the virtual environment and runs the main entry point of the Immich app
# Supports optional profiling mode via env `RUN_PROFILING=1` or flag `--profile` / `-p`

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_SCRIPT="$SCRIPT_DIR/main.py"

# Parse args for --profile / -p / --no-profile; remaining args are passed to the app
 # Default: profiling OFF unless explicitly enabled by env or flag
PROFILE=${RUN_PROFILING:-0}
ARGS=()
for a in "$@"; do
  case "$a" in
    --no-profile)
      PROFILE=0
      ;;
    --profile|-p)
      PROFILE=1
      ;;
    *)
      ARGS+=("$a")
      ;;
  esac
done

if [ ! -d "$VENV_DIR" ]; then
  echo "ERROR: Virtual environment not found in $VENV_DIR"
  echo "Tip: run ./setup_venv.sh to create the virtual environment."
  exit 1
fi

source "$VENV_DIR/bin/activate"

if [ "${PROFILE}" = "1" ]; then
  echo "[run_app] Running in profiling mode (cProfile)."
  # Require the profiling helper to be present and executable. Fail fast if not.
  PROFILE_HELPER="$SCRIPT_DIR/scripts/devtools/profiling/profile_run.sh"
  if [ -x "$PROFILE_HELPER" ]; then
    cd "$SCRIPT_DIR"
    bash "$PROFILE_HELPER" "${ARGS[@]}"
  else
    echo "[run_app] ERROR: required profiling helper not found or not executable: $PROFILE_HELPER" >&2
    exit 2
  fi
else
  cd "$SCRIPT_DIR"
  # Run the package as a module to ensure absolute package imports resolve
  # consistently in CI and local environments.
  python -m immich_autotag "${ARGS[@]}"
fi
