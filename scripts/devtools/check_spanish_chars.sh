#!/bin/bash
# Spanish language character check (robust project root detection)
# Usage: ./check_spanish_chars.sh [target_dir]

# Detect project root (directory containing this script, then up one level)
set -e
set -x
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR" | xargs dirname)"

# Set the target directory to project root unless overridden by argument
TARGET_DIR="${1:-$PROJECT_ROOT}"

# Exclude common build and dependency folders
EXCLUDES=".git,.venv,node_modules,dist,build,logs_local,jenkins_logs,__pycache__"

# Find Spanish/accented characters in source code
EXCLUDE_ARGS=$(printf -- '--exclude-dir=%s ' $(echo $EXCLUDES | tr ',' ' '))
spanish_matches=$(grep -r -n -I -E '[áéíóúÁÉÍÓÚñÑüÜ¿¡]' "$TARGET_DIR" $EXCLUDE_ARGS || true)

if [ -n "$spanish_matches" ]; then
    echo '❌ Spanish language characters detected in the following files/lines:'
    echo "$spanish_matches"
    # Count unique files with matches
    file_count=$(echo "$spanish_matches" | cut -d: -f1 | sort | uniq | wc -l)
    echo "Files remaining to translate: $file_count"
    exit 1
else
    echo "✅ No Spanish language characters detected."
    echo "Files remaining to translate: 0"
    exit 0
fi
