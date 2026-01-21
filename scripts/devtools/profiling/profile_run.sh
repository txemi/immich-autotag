#!/bin/bash
# Run the main script with cProfile and save the result to profile.stats
# Consolidated helper for CI: saves profile.stats into `logs_local/profiling/`
# and prints a short pstats summary (top 30 cumulative).

set -euo pipefail

OUTPUT_FILE="profile.stats"

# Allow CI or local users to disable profiling by setting SKIP_PROFILING=1
# Default to skipping profiling to avoid OOM in CI environments.
SKIP_PROFILING="${SKIP_PROFILING:-1}"

if [ "$SKIP_PROFILING" = "1" ] || [ "$SKIP_PROFILING" = "true" ]; then
	echo "[profile_run] SKIP_PROFILING set -> running package without cProfile"
	# Run package as module to ensure imports resolve consistently in CI
	python -m immich_autotag "$@"
else
	echo "[profile_run] Running cProfile -> $OUTPUT_FILE"
	# Profile the package module rather than the main.py script
	python -m cProfile -o "$OUTPUT_FILE" -s cumulative -m immich_autotag "$@"
fi

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

# Also maintain a `latest` copy for easy access and tooling that expects a stable path.
LATEST_DIR="logs_local/profiling/latest"
mkdir -p "$LATEST_DIR"
cp "$ART_DIR/$OUTPUT_FILE" "$LATEST_DIR/$OUTPUT_FILE"

# Write metadata for this profile run (timestamp, git SHA if available, branch env)
METAFILE="$LATEST_DIR/metadata.txt"
TS_HUMAN=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
GIT_BRANCH="${GIT_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)}"
echo "timestamp: $TS_HUMAN" > "$METAFILE"
echo "profile_path: $ART_DIR/$OUTPUT_FILE" >> "$METAFILE"
echo "git_sha: $GIT_SHA" >> "$METAFILE"
echo "git_branch: $GIT_BRANCH" >> "$METAFILE"
echo "[profile_run] Latest copy and metadata written to $LATEST_DIR"

