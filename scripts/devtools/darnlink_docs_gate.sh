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
# as THREE passes (mode=max = the union of all axes; `set -e` aborts on the first):
#
#     darnlink check .                          # integrity + strict axis
#     darnlink . --robustify --create-frontmatter   # create-frontmatter axis
#     darnlink web-check . --online             # web axis (cross-repo links; skip: DARNLINK_SKIP_WEB=1)
#
# It fails the build if ANY internal Markdown link points at a file that does
# not carry a `uuid` in its frontmatter. In other words: every link target is
# uuid-anchored, so no refactor (moving/renaming a file or a whole subtree) can
# ever silently break a link — darnlink can always re-anchor by uuid. The added
# `check` pass also covers integrity + strict (broken robust links / un-anchored);
# it additionally requires that *linkable* targets be uuid-bearing.
# Exit 0 = clean, non-zero = findings. To fix locally (writes uuids):
#
#     uvx --from "git+https://github.com/txemi/darnlink@v0.20.4" darnlink . --robustify --create-frontmatter --write
#
# Shared by the three gates so the logic lives in one place:
#   - pre-commit  (.pre-commit-config.yaml)
#   - Jenkins     (Jenkinsfile stage 'Quality Gate (Docs Links)')
#   - GitHub Actions (.github/workflows/docs-links.yml)
#
# Env overrides:
#   DARNLINK_REF   git ref of darnlink to use   (default: immutable SHA of v0.20.4)
#   DARNLINK_FROM  full uvx --from spec (path or git+)  (default: the pinned SHA)
#                  e.g. DARNLINK_FROM=/path/to/local/darnlink for local dev
#
# Args:
#   $1  scan root (default: repo root '.') — darnlink needs the whole tree to
#       build the uuid index, so scan the repo root, not a single file.
set -euo pipefail

# Pinned to an immutable commit SHA (== tag v0.20.4). Tags can be force-moved,
# which would weaken CI reproducibility / supply-chain integrity, so we pin the
# SHA and keep the tag only as a human-readable note.
#
# ^ That note is the WHOLE point of the tag comment, and it went stale for four
# releases: the SHA was bumped v0.16.0 -> v0.20.3 while this line kept saying
# v0.16.0. A pin whose human-readable note lies is worse than one with no note --
# it is what an auditor reads instead of resolving the SHA. When you bump the SHA
# on the line below, bump BOTH mentions or neither.
DARNLINK_REF="${DARNLINK_REF:-57f110fb665c826d560746ce86ebd22a92a78744}" # v0.20.4
DARNLINK_FROM="${DARNLINK_FROM:-git+https://github.com/txemi/darnlink@${DARNLINK_REF}}"
SCAN_ROOT="${1:-.}"

# EXCLUDES: directories the gate must not walk.
#
# `logs_local/` is RUNTIME OUTPUT, not documentation: the batch writes a fresh
# `immich_autotag_links.md` (plus an `_archive/cycle-*/` tree) on every pass, and
# `.gitignore` already excludes it -- none of it is tracked. Without this the gate
# demanded `web-uuid` anchors on files the job had just generated, so the pipeline
# failed on its own output: build #358 of ops/batch-processing died with 24 pending
# anchors, every one of them under logs_local/. Anchoring them would not have fixed
# anything either -- the next run regenerates them unanchored.
#
# This is repo-wide on purpose, not branch-specific: Jenkinsfile runs run_app.sh on
# EVERY branch and archives logs_local/*_PID*/**, so main produces them too and would
# hit the same wall as soon as it got past the earlier gates.
#
# ONE entry, not two. The archived cycles live at logs_local/_archive/cycle-*, so they
# are already covered. Excluding '_archive' as well would be redundant here and too
# broad everywhere else: excludes are directory-NAME globs, so it would silently skip
# any _archive/ added anywhere in the repo later. Narrow beats convenient in a gate.
DARNLINK_EXCLUDES=(--exclude 'logs_local')

echo "darnlink docs-link gate — scanning '${SCAN_ROOT}' via '${DARNLINK_FROM}' (max: fail-closed, read-only)"
# mode=max = check (integrity + strict) UNION create-frontmatter UNION web. `check` catches broken
# robust links + un-anchored plain links; the 2nd pass catches plain links whose target has no uuid;
# the 3rd (web) verifies cross-repo GitHub links still resolve to the destination's uuid (read online).
# `set -e` aborts on the first failure -> a true superset of all axes.
uvx --from "${DARNLINK_FROM}" darnlink check "${SCAN_ROOT}" "${DARNLINK_EXCLUDES[@]}"
uvx --from "${DARNLINK_FROM}" darnlink "${SCAN_ROOT}" "${DARNLINK_EXCLUDES[@]}" --robustify --create-frontmatter

# DANGLING axis (v0.20.x) — the one this gate was MISSING, and the reason 108 dead links lived here
# unnoticed for months. `check` reports a plain link to a NON-EXISTENT file under `dangling`, but its
# exit code ignores that axis: the build went green while the links were dead. It is not a category
# the other passes cover — a dangling link is neither `unresolvable` nor `robustify`, so it fell
# through every one of them.
#
# Read the axis out of --json, which is what the shared recipe does, and fail closed on any finding.
# mktemp, NOT a fixed /tmp path: the pre-commit and pre-push hooks run on developer
# machines where several worktrees can commit at once, and a shared path lets one run
# overwrite another's report -- a red build could read a clean JSON and go green.
DL_JSON="$(mktemp)"; trap 'rm -f "${DL_JSON}"' EXIT
uvx --from "${DARNLINK_FROM}" darnlink check "${SCAN_ROOT}" "${DARNLINK_EXCLUDES[@]}" --json > "${DL_JSON}"
python3 - "${DL_JSON}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
f = (d.get("dangling") or {}).get("findings") or []
if f:
    print(f"darnlink dangling: {len(f)} link(s) point at a path that does not exist:", file=sys.stderr)
    for x in f[:20]:
        print(f"  {x.get('file','?')}:{x.get('line','?')}  {x.get('detail','')}", file=sys.stderr)
    if len(f) > 20:
        print(f"  ... and {len(f)-20} more", file=sys.stderr)
    sys.exit(1)
print("darnlink dangling: 0 -> ok")
PY

# WEB axis: cross-repo links to PUBLIC repos must still resolve to the destination file's uuid (read
# online, tokenless). Anchored with `<!-- web-uuid: X -->`. Fail-closed on a broken cross-repo link.
# Skippable offline (DARNLINK_SKIP_WEB=1, e.g. a disconnected pre-commit); pre-push/CI always has network.
if [ "${DARNLINK_SKIP_WEB:-0}" != "1" ]; then
	exec uvx --from "${DARNLINK_FROM}" darnlink web-check "${SCAN_ROOT}" "${DARNLINK_EXCLUDES[@]}" --online
fi
