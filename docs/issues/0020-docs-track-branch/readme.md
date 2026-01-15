# Issue 0020: docs-track Branch - Documentation Tracking

## Purpose

The `docs-track` branch serves as a coordination point for documentation (issues, plans, designs, changelog) that can progress to main quickly without waiting for implementation.

## Problem

When features take time to implement, their documentation gets delayed in reaching main. This makes planning and issue tracking less visible.

## Solution

Use `docs-track` as a staging area for documentation-only commits that can be merged to main/develop frequently.

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

### Merging to main

When stabilizing a feature for main/develop merge:
- Check if `docs-track` contains only documentation
- If yes: include it in your merge/PR
- If no: create separate PR for docs-track

## Benefits

1. **Avoid issue number conflicts**: Everyone increments from the same point
2. **Documentation reaches main faster**: No need to wait for implementation
3. **Better visibility**: Plans and designs visible in main branch
4. **Low effort**: Just use docs-track as base, no complex workflows

## Status

- **Type**: Workflow experiment
- **Active**: Yes
- **Scope**: Solo developer for now, may be documented in CONTRIBUTING.md if successful
