#!/bin/bash
# Run quality gate sequentially: RELAXED, then TARGET (stop on failure)
set -e

SCRIPT_DIR="$(dirname "$0")"
QGATE="$SCRIPT_DIR/quality_gate.sh"

# Run RELAXED
bash "$QGATE" --level=RELAXED --mode=CHECK "$@"

# Run TARGET
bash "$QGATE" --level=TARGET --mode=CHECK "$@"

echo "Both RELAXED and TARGET quality gates passed."
