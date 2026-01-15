#!/bin/bash
# Run the main script with cProfile and save the result to profile.stats
# Consolidated helper for CI: saves profile.stats into `logs_local/profiling/`
# and prints a short pstats summary (top 30 cumulative).

set -euo pipefail

OUTPUT_FILE="profile.stats"

echo "[profile_run] Running cProfile -> $OUTPUT_FILE"
python -m cProfile -o "$OUTPUT_FILE" -s cumulative main.py "$@"

if [ ! -f "$OUTPUT_FILE" ]; then
	echo "[profile_run] ERROR: profiling output not found: $OUTPUT_FILE" >&2
	exit 1
fi

# Create an archive location that Jenkins already archives via `logs_local/**/*`
TS=$(date -u +"%Y%m%dT%H%M%SZ")
ART_DIR="logs_local/profiling/$TS"
mkdir -p "$ART_DIR"
mv "$OUTPUT_FILE" "$ART_DIR/"

echo "[profile_run] Profile saved to $ART_DIR/$OUTPUT_FILE"

echo "[profile_run] Producing top-30 cumulative pstats summary (printed below)"
python - <<PY
import pstats
from pstats import SortKey
ps = pstats.Stats('$ART_DIR/$OUTPUT_FILE')
ps.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats(30)
PY

echo "To visualize it graphically, install snakeviz and run locally:"
echo "  snakeviz $ART_DIR/$OUTPUT_FILE"

