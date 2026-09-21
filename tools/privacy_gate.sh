#!/usr/bin/env bash
# Privacy gate: blocks private references from reaching this public repo. Same script for every place
# that runs it (GitHub Actions, Jenkins, by hand); the callers only decide where the inputs come from.
#
# Inputs (environment):
#   DENYLIST_FILE   REQUIRED. A file with one extended regex per line. It is a secret: a list of
#                   private names cannot live in the repository it protects.
#   PR_TEXT_FILE    optional. A file holding the PR title and description.
#   BASE_SHA        optional. Commit messages in BASE_SHA..HEAD are judged.
#   BASELINE_FILE   optional. Default .github/privacy-gate-baseline.txt (file:line entries).
#
# Three surfaces, in order of how hard they are to undo: the PR text (rendered publicly, indexed, and
# never fully retractable: an edit keeps the old text readable through the API), commit messages
# (cannot change after a push without rewriting history), tracked files (permanent in git history).
#
# Two deliberate choices:
#   - FAIL-CLOSED whenever the gate cannot really judge: a missing or empty list, a list with CRLF line
#     ends or with a pattern that is not a valid extended regex (grep then exits 2 and matches NOTHING,
#     which reads as "clean"), a PR_TEXT_FILE that does not exist, a BASE_SHA that does not resolve.
#     Exit 2 means "could not judge"; exit 1 means "found something".
#   - NEVER PRINT THE MATCH. Logs on a public repo are public, so only file:line is reported.
set -uo pipefail
cd "$(dirname "$0")/.."
# BYTE order, not locale order: `comm` needs both inputs sorted with its own collation.
export LC_ALL=C
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if [ -z "${DENYLIST_FILE:-}" ] || [ ! -f "$DENYLIST_FILE" ]; then
  echo "ERROR: DENYLIST_FILE is not set or is not a file. Failing closed:"
  echo "a privacy gate with no patterns would report success while checking nothing."
  exit 1
fi
grep -v '^[[:space:]]*$' "$DENYLIST_FILE" > "$work/denylist.txt" || true
# Re-check AFTER stripping blank lines: a list holding only whitespace passes a -z test and then
# leaves zero patterns, and GNU grep -f with an empty pattern file matches NOTHING (exit 1), so every
# surface would report "clean" while checking nothing. (ugrep does the opposite on the same input, so
# a local test can disagree with a runner: hence an explicit check instead of relying on either.)
if [ ! -s "$work/denylist.txt" ]; then
  echo "ERROR: the deny list contains no usable patterns (blank or whitespace only). Failing closed."
  exit 1
fi
if grep -q $'\r' "$work/denylist.txt"; then
  echo "ERROR: the deny list has CRLF line ends: every pattern would carry a trailing CR and match"
  echo "nothing. Failing closed. Convert it to LF."
  exit 2
fi
# One bad pattern disables the WHOLE scan: grep exits 2 and prints no match. Probe the list first.
grep -qiEf "$work/denylist.txt" /dev/null 2>/dev/null
if [ "$?" -ne 1 ]; then
  echo "ERROR: the deny list holds a pattern that is not a valid extended regex. Failing closed."
  exit 2
fi
echo "Patterns loaded: $(wc -l < "$work/denylist.txt") (contents intentionally not printed)"

fail=0

# Baseline of pre-existing violations as file:line, never the offending text, so it is safe in a
# public repo. It may only shrink. Brittle on purpose: if a line moves, the entry stops matching and
# the case comes back for a fresh look.
BASELINE="${BASELINE_FILE:-.github/privacy-gate-baseline.txt}"
grep -v '^[[:space:]]*\(#\|$\)' "$BASELINE" 2>/dev/null | sort -u > "$work/baseline.txt" || : > "$work/baseline.txt"
echo "Baseline entries: $(wc -l < "$work/baseline.txt")"

echo "--- tracked files ---"
git ls-files -z | xargs -0 grep -nIiEf "$work/denylist.txt" 2>/dev/null \
  | cut -d: -f1,2 | sort -u > "$work/all_hits.txt" || :
comm -23 "$work/all_hits.txt" "$work/baseline.txt" > "$work/hits.txt"
if [ -s "$work/hits.txt" ]; then
  sed 's/^/  /' "$work/hits.txt"
  echo "ERROR: private reference(s) found in tracked files (see file:line above)"
  fail=1
else
  echo "  clean ($(comm -12 "$work/all_hits.txt" "$work/baseline.txt" | wc -l) known, in baseline)"
fi
# A baseline entry that no longer matches is settled debt: remove it so it cannot come back.
if [ -n "$(comm -13 "$work/all_hits.txt" "$work/baseline.txt")" ]; then
  echo "WARNING: baseline entries no longer matching; remove them from $BASELINE:"
  comm -13 "$work/all_hits.txt" "$work/baseline.txt" | sed 's/^/  /'
fi

if [ -n "${PR_TEXT_FILE:-}" ]; then
  echo "--- pull request title/body ---"
  if [ ! -f "$PR_TEXT_FILE" ]; then
    echo "ERROR: PR_TEXT_FILE is set but is not a file. Failing closed."
    exit 2
  fi
  grep -qiEf "$work/denylist.txt" "$PR_TEXT_FILE"
  case "$?" in
    0) echo "ERROR: private reference in the PR title or body. Edit it BEFORE merging:"
       echo "editing later does not remove it (the old revision stays readable via the API)."
       fail=1 ;;
    1) echo "  clean" ;;
    *) echo "ERROR: could not scan the PR text. Failing closed."; exit 2 ;;
  esac
fi

if [ -n "${BASE_SHA:-}" ]; then
  echo "--- commit messages ---"
  # An all-zero sha (a push that creates a branch) or any ref that does not resolve: there is no
  # range to read, and `git log` failing into a pipe would read as "clean".
  if ! git rev-parse --verify --quiet "${BASE_SHA}^{commit}" >/dev/null; then
    echo "ERROR: BASE_SHA does not resolve to a commit. Failing closed."
    exit 2
  fi
  if ! git log --format='%s%n%b' "${BASE_SHA}..HEAD" > "$work/messages.txt"; then
    echo "ERROR: could not read the commit messages. Failing closed."
    exit 2
  fi
  grep -qiEf "$work/denylist.txt" "$work/messages.txt"
  case "$?" in
    0) echo "ERROR: private reference in a commit message: amend or rebase before merging."
       fail=1 ;;
    1) echo "  clean" ;;
    *) echo "ERROR: could not scan the commit messages. Failing closed."; exit 2 ;;
  esac
fi

exit "$fail"
