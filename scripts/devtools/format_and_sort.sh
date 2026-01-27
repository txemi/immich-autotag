#!/bin/bash
# Lightweight wrapper for the devtools formatter script so the workspace task can find `scripts/format_and_sort.sh`
SCRIPT_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1
	pwd -P
)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [[ "$*" != *--level=* ]] && [[ "$*" != *" -l "* ]]; then
	echo "[ERROR] You must specify --level=LEVEL or -l LEVEL (STRICT, RELAXED, TARGET)"
	exit 2
fi
if [[ "$*" != *--mode=* ]] && [[ "$*" != *" -m "* ]]; then
	echo "[ERROR] You must specify --mode=MODE or -m MODE (CHECK, APPLY)"
	exit 2
fi
"$SCRIPT_DIR/quality_gate.sh" "$@"
