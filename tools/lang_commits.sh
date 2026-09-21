#!/usr/bin/env bash
# English-only gate for commit messages, ONE MESSAGE AT A TIME.
#
#   lang_commits.sh <base> [<head>]   judge every commit in <base>..<head> (head defaults to HEAD)
#   lang_commits.sh --last <commit>   judge one commit (a push that creates a branch has no base)
#
# Concatenating the range and judging it as one text is how a single English message hides a
# non-English one, so each message is its own input. No --strict: layer 3 blocks honest English on a
# subject line. Same script for every place that runs it (GitHub Actions, Jenkins, by hand).
# Pin: tools/darnlang_ref.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
# shellcheck source=darnlang_ref.sh
. tools/darnlang_ref.sh
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Resolve in a step of its OWN: `uvx --from <ref> darnlang ...` in one call cannot tell "could not
# resolve" (uvx exits 1) from "found something" (darnlang exits 1).
uv tool install --quiet "$DARNLANG_REF"
export PATH="$(uv tool dir --bin):$PATH"

if [ "${1:-}" = "--last" ]; then
  shas="$(git rev-parse --verify "${2:?usage: lang_commits.sh --last <commit>}^{commit}")"
else
  base="${1:?usage: lang_commits.sh <base> [<head>] | --last <commit>}"
  shas="$(git log --format=%H "${base}..${2:-HEAD}")"
fi

fail=0
for sha in $shas; do
  git log -1 --format=%B "$sha" > "$tmp/one.txt"
  darnlang prose "$tmp/one.txt" --label "commit message $sha" || fail=1
done
exit "$fail"
