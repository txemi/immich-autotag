#!/usr/bin/env bash
#
# darnlink docs-link gate
# ------------------------
# Read-only quality gate for the documentation's Markdown links.
#
# darnlink anchors each internal Markdown link to the target file's `uuid`
# (frontmatter + an inline `<!-- uuid: ... -->` comment). When a file moves,
# the path in the link goes stale but the uuid still points at the target.
# This gate runs darnlink in its default *report* mode (NO --write): it exits
# non-zero if any anchored link needs repair, has an unresolved uuid, or a
# target has invalid frontmatter. To fix locally:
#
#     uvx --from "git+https://github.com/txemi/darnlink@v0.1.1" darnlink . --write
#
# Shared by the three gates so the logic lives in one place:
#   - pre-commit  (.pre-commit-config.yaml)
#   - Jenkins     (Jenkinsfile stage 'Quality Gate (Docs Links)')
#   - GitHub Actions (.github/workflows/docs-links.yml)
#
# Env overrides:
#   DARNLINK_REF   git tag/branch of darnlink to use   (default: v0.1.1)
#   DARNLINK_FROM  full uvx --from spec (path or git+)  (default: the pinned tag)
#                  e.g. DARNLINK_FROM=/path/to/local/darnlink for local dev
#
# Args:
#   $1  scan root (default: repo root '.') — darnlink needs the whole tree to
#       build the uuid index, so scan the repo root, not a single file.
set -euo pipefail

DARNLINK_REF="${DARNLINK_REF:-v0.1.1}"
DARNLINK_FROM="${DARNLINK_FROM:-git+https://github.com/txemi/darnlink@${DARNLINK_REF}}"
SCAN_ROOT="${1:-.}"

echo "darnlink docs-link gate — scanning '${SCAN_ROOT}' via '${DARNLINK_FROM}' (read-only)"
exec uvx --from "${DARNLINK_FROM}" darnlink "${SCAN_ROOT}"
