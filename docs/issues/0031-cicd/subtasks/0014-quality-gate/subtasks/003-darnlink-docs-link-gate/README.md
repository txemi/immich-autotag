# 003 · darnlink docs-link gate

A read-only quality gate that keeps the documentation's internal Markdown links
from silently breaking when files move.

## Problem

The docs tree is large and gets reorganized. When a `.md` file is moved or
renamed, relative links pointing at it go stale and nobody notices until a
reader hits a 404. This has already required manual cleanup (see
`../../0015-github-actions-pypi-publishing/subtasks/003-clean-up/manual_cleanup_links.md`).

## What darnlink does

[darnlink](https://github.com/txemi/darnlink) anchors each internal Markdown
link to the target file's `uuid` (added to the target's frontmatter, plus an
inline `<!-- uuid: ... -->` comment next to the link). The link stays a normal,
clickable Markdown link. When a file moves, the path is stale but the uuid still
resolves, so darnlink can repair the path deterministically — no database, no
editor lock-in. It is **not** a broken-link checker: it maintains the
*move-resilience* of links it has anchored.

## What was done

1. **Robustify (one-off):** `darnlink docs/ --robustify --create-frontmatter --write`
   anchored the existing internal links under `docs/` (small footprint — a
   handful of files gained a `uuid` and their links an anchor). Scope is `docs/`
   only, so the repo-root `README.md` (rendered on the GitHub landing page) is
   left untouched.
2. **Gate (ongoing):** `scripts/devtools/darnlink_docs_gate.sh` runs darnlink in
   its default *report* mode (no `--write`) over the repo. It exits non-zero if
   any anchored link needs repair, is unresolved, or a target has invalid
   frontmatter. The darnlink version is pinned (`v0.24.0`).

## Where it runs (one script, three gates)

| Gate | Wiring |
|------|--------|
| pre-commit | `.pre-commit-config.yaml` → hook `darnlink-docs-links` |
| Jenkins | `Jenkinsfile` stage `Quality Gate (Docs Links)` |
| GitHub Actions | `.github/workflows/docs-links.yml` (independent of the disabled test CI — needs no Immich client lib) |

## Fixing a failure

If the gate is red, a doc moved and a link is stale. Repair and commit:

```bash
uvx --from "git+https://github.com/txemi/darnlink@v0.24.0" darnlink . --write
```

## Status

- [x] Robustify `docs/` (one-off).
- [x] Shared gate script + wired into pre-commit, Jenkins, GitHub Actions.
- [ ] Verify the three gates run green in CI after merge.
