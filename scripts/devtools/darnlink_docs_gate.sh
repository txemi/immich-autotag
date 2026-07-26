#!/usr/bin/env bash
#
# darnlink docs-link gate
# ------------------------
# Read-only quality gate for the documentation's Markdown links.
#
# darnlink anchors each internal Markdown link to the target file's `uuid`
# (frontmatter + an inline `<!-- uuid: ... -->` comment). When a file moves,
# the path in the link goes stale but the uuid still points at the target.
#
# This gate runs at the MAXIMUM (fail-closed) level, report-only (NO --write),
# as TWO passes (mode=max = the union of both axes; `set -e` aborts on the first):
#
#     darnlink check .                          # integrity + strict axis
#     darnlink . --robustify --create-frontmatter   # create-frontmatter axis
#
# It fails the build if ANY internal Markdown link points at a file that does
# not carry a `uuid` in its frontmatter. In other words: every link target is
# uuid-anchored, so no refactor (moving/renaming a file or a whole subtree) can
# ever silently break a link — darnlink can always re-anchor by uuid. The added
# `check` pass also covers integrity + strict (broken robust links / un-anchored);
# it additionally requires that *linkable* targets be uuid-bearing.
# Exit 0 = clean, non-zero = findings. To fix locally (writes uuids):
#
#     uvx --from "git+https://github.com/txemi/darnlink@v0.16.0" darnlink . --robustify --create-frontmatter --write
#
# Shared by the three gates so the logic lives in one place:
#   - pre-commit  (.pre-commit-config.yaml)
#   - Jenkins     (Jenkinsfile stage 'Quality Gate (Docs Links)')
#   - GitHub Actions (.github/workflows/docs-links.yml)
#
# Env overrides:
#   DARNLINK_REF   git ref of darnlink to use   (default: immutable SHA of v0.16.0)
#   DARNLINK_FROM  full uvx --from spec (path or git+)  (default: the pinned SHA)
#                  e.g. DARNLINK_FROM=/path/to/local/darnlink for local dev
#
# Args:
#   $1  scan root (default: repo root '.') — darnlink needs the whole tree to
#       build the uuid index, so scan the repo root, not a single file.
set -euo pipefail

# Pinned to an immutable commit SHA (== tag v0.16.0). Tags can be force-moved,
# which would weaken CI reproducibility / supply-chain integrity, so we pin the
# SHA and keep the tag only as a human-readable note.
DARNLINK_REF="${DARNLINK_REF:-bda64d172b05cb546f485a0c4be40d8763796354}"  # v0.16.0
DARNLINK_FROM="${DARNLINK_FROM:-git+https://github.com/txemi/darnlink@${DARNLINK_REF}}"
SCAN_ROOT="${1:-.}"

echo "darnlink docs-link gate — scanning '${SCAN_ROOT}' via '${DARNLINK_FROM}' (max: fail-closed, read-only)"
# mode=max = check (integrity + strict) UNION create-frontmatter. `check` catches broken robust
# links + un-anchored plain links; the second pass catches plain links whose target has no uuid.
# `set -e` aborts on the first failure -> a true superset of both axes.
uvx --from "${DARNLINK_FROM}" darnlink check "${SCAN_ROOT}"
exec uvx --from "${DARNLINK_FROM}" darnlink "${SCAN_ROOT}" --robustify --create-frontmatter
