# Issue 0020: docs-track Branch - Documentation Tracking

## Purpose

The `docs-track` branch serves as a coordination point for documentation (issues, plans, designs, changelog) that can progress to main quickly without waiting for implementation.

## Problem

When features take time to implement, their documentation gets delayed in reaching main. This makes planning and issue tracking less visible.

## Solution

Use `docs-track` as a staging area for documentation-only commits that can be merged to main/develop frequently.

## Policy

**What goes in docs-track (planning and proposals, no implementation assumed):**
- ✅ New issues and planning
- ✅ Roadmap and future vision
- ✅ Design documents (proposals)
- ✅ CHANGELOG entries

**What doesn't go in docs-track:**
- ❌ Implementation code
- ❌ Documentation that assumes unmerged features exist, just plan analysis or design


**Key rule:** Documentation must not assume anything is already implemented. If it says "the system does X", X must already be merged in docs-track or independent.

## Quick Policies (one-line rules)

- `docs-track` is docs-only: never include code or build artifacts.
- Keep entries generic and planning-focused; avoid claiming features are implemented unless merged.
- Prefer concise, actionable docs: issues, designs, changelog notes, roadmaps.
- If documentation must be published before implementation, put it here; implementation goes to a feature branch.
- Keep commits small and descriptive: `docs: add issue 0021 - profiling plan`.

## Daily Checklist (for contributors)

- 1) Create docs branches from `docs-track` for new plans or designs.
- 2) Add only documentation files or edits; run a quick `git diff` to verify no code changes.
- 3) Merge into `docs-track` when ready using `--ff-only` or cherry-pick.
- 4) If you need to implement code later, create a feature branch from `main` or `develop` and reference the docs issue.

## Merge & Sync Guidelines

- `docs-track` should be kept reasonably up-to-date by regularly merging its changes into feature branches when those branches need current documentation context.
- Merging `docs-track` into `main`/`develop` is safe because it contains no code. Use fast-forward merges or small PRs for visibility.
- If `docs-track` diverges for a long time, reconcile by merging the up-to-date stable branch (e.g., `main`) into `docs-track` to avoid surprises.

## When code is required

- If documentation depends on code (examples, scripts), keep the docs on `docs-track` but place code in a separate feature branch. Link the feature branch in the docs.
- Do not commit code to `docs-track`. If someone accidentally adds code, revert it and move the change to a feature branch.

## Short example (recommended workflow)

1. `git checkout docs-track && git checkout -b docs/0021-profiling`
2. Add `docs/issues/0021` contents and `CHANGELOG` note; commit with `docs:` prefix.
3. Merge into `docs-track` once reviewed: `git checkout docs-track && git merge --ff-only docs/0021-profiling`.
4. Later, implement in `feat/0021-profiling` and reference `docs/issues/0021` in commits.


## Usage

### Creating new documentation

```bash
# 1. Branch from docs-track
git checkout docs-track
git checkout -b my-new-feature

# 2. First commits: documentation only
git commit -m "docs: Add issue 0021 - My feature"
git commit -m "docs: Add technical design"

# 3. Advance docs-track (when ready)
git checkout docs-track
git merge --ff-only my-new-feature
# Or cherry-pick the doc commits

# 4. Continue with implementation
git checkout my-new-feature
git commit -m "feat: Implement feature"
```

### Checking latest issue number

```bash
# View registry to get next available number
git show docs-track:docs/issues/registry.md
```

### Syncing documentation while working on a feature

If you're working on a feature and notice `docs-track` is ahead:

```bash
# 1. Check what's new in docs-track
git log --oneline docs-track ^HEAD

# 2. If only documentation (no code changes)
git merge docs-track

# 3. Continue with your implementation
# Now you have complete documentation context
```

**Important:** Only merge if you're sure it's documentation-only. If coupled to another feature, keep your branches separate.

This lets you:
- See latest documentation plans
- Get updated issue numbering
- Understand context before implementing
- All without pulling implementation code

## Key Benefits

When you follow this approach:

1. **Documentation reaches main faster**: docs-track merges frequently without waiting for implementation
2. **No separate documentation PRs needed**: Documentation comes naturally as part of feature merges
3. **Fresh planning always visible**: main branch always shows latest plans, roadmaps, and designs
4. **Minimal effort**: Just use docs-track as base branch, no extra management needed
5. **Maximum visibility**: Anyone checking main branch sees current planning and documentation

By incorporating docs-track early in your feature branches, you ensure that documentation and planning flow naturally into main alongside implementation, eliminating friction and keeping planning visible with minimal overhead.

## Status

- **Type**: Workflow experiment
- **Active**: Yes
- **Scope**: Solo developer for now, may be documented in CONTRIBUTING.md if successful
