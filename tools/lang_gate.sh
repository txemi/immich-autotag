#!/usr/bin/env bash
# English-only gate for the text of a pull request.
#
#   lang_gate.sh pr-text <file>   judge a file holding the PR title and description
#
# The file gate for the tracked tree is `check_no_spanish_chars` in the Python quality gate; it is
# better than darnlang on files and stays as it is. This covers what that check cannot see: what is
# written straight into the forge. Same script for every place that runs it. Pin: tools/darnlang_ref.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=darnlang_ref.sh
. tools/darnlang_ref.sh

case "${1:-}" in
  pr-text)
    f="${2:?usage: lang_gate.sh pr-text <file>}"
    uv tool install --quiet "$DARNLANG_REF"
    export PATH="$(uv tool dir --bin):$PATH"
    darnlang prose "$f" --label "PR title/description"
    ;;
  *)
    echo "usage: lang_gate.sh pr-text <file>" >&2
    exit 2
    ;;
esac
