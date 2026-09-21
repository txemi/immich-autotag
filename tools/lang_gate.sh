#!/usr/bin/env bash
# English-only gate. One script for the workflows, Jenkins and a hand run.
#   lang_gate.sh tree            the tracked files, against the baseline
#   lang_gate.sh pr-text <file>  a PR title and description, strict
# tools/darnlang_ref.sh names what to install: DARNLANG_REF, and DARNLANG_STRICT_REF when the
# strict build is not simply "darnlang[strict] @ $DARNLANG_REF" (this repo installs itself).
set -euo pipefail
cd "$(dirname "$0")/.."
. tools/darnlang_ref.sh
# Install first, judge after: with `uvx --from`, a failed install (rc 1) reads as a finding (rc 1).
uv tool install --quiet --force "${DARNLANG_STRICT_REF:-darnlang[strict] @ $DARNLANG_REF}"
export PATH="$(uv tool dir --bin):$PATH"
case "${1:-}" in
  tree)
    darnlang check --ext all
    ;;
  pr-text)
    darnlang prose "${2:?usage: lang_gate.sh pr-text <file>}" --strict --label "PR title/description"
    ;;
  *)
    echo "usage: lang_gate.sh tree | pr-text <file>" >&2
    exit 2
    ;;
esac
