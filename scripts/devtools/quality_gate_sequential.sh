#!/bin/bash
# Run quality gate sequentially: RELAXED, then TARGET (stop on failure)
set -e

SCRIPT_DIR="$(dirname "$0")"
QGATE="$SCRIPT_DIR/quality_gate.sh"


# Run STANDARD
bash "$QGATE" --level=STANDARD --mode=CHECK "$@"

# Run TARGET
bash "$QGATE" --level=TARGET --mode=CHECK "$@"

echo "Both RELAXED and TARGET quality gates passed."
