#!/bin/bash
# Lightweight wrapper for the devtools formatter script so the workspace task can find `scripts/format_and_sort.sh`
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
"$REPO_ROOT/scripts/devtools/quality_gate.sh" "$@"
