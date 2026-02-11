#!/bin/bash
# Ordena y elimina duplicados en spanish_words.txt usando la ruta del propio script
set -e
set -x
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORDS_FILE="$SCRIPT_DIR/spanish_words.txt"
SORTED_FILE="$SCRIPT_DIR/spanish_words_sorted.txt"
sort "$WORDS_FILE" | uniq > "$SORTED_FILE"
mv "$SORTED_FILE" "$WORDS_FILE"
