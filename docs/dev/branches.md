# Branch Strategy and Special Branches

This document outlines the branching strategy used in immich-autotag, particularly the special-purpose branches that should NOT be deleted even if they appear redundant from a commit history perspective.

## Core Branches

### `main`
- **Purpose:** Stable, production-ready code
- **Policy:** Only merge from tested feature branches or develop
- **Protection:** This is the default branch

### `develop`
- **Purpose:** Integration branch for features under development
- **Policy:** Merge tested features here before promoting to main
- **Status:** Active (convention-based)

## Special-Purpose Branches

### `docs-track`
- **Purpose:** Coordination point for **documentation-only changes** (issues, plans, designs, changelog)
- **Key Rule:** Documentation progresses independently of code implementation
- **Scope:** Issue templates, CHANGELOG entries, architectural designs, plans—**NO code**
- **Benefits:**
  - Documentation can be prepared and reviewed before implementation starts
  - Changes can be merged to main/develop quickly without waiting for code
  - Keeps documentation versions synchronized across branches
- **Policy:** 
  - Use `--ff-only` or `--no-ff` merges to main/develop (fast-forward or no fast-forward)
  - Never add code or build artifacts
  - Keep reasonably up-to-date with main
  
 **For detailed guidelines:** See [Issue 0020 — docs-track Branch](../issues/0020-docs-track-branch/readme.md)

## Feature / Experimental Branches

### `feature/*` branches
- **Purpose:** Development branches for specific features
- **Naming:** `feature/user-group-policies`, `feature/auto-album-creation-from-date`, etc.
- **Policy:** Create from develop, merge back once tested

### `perf/*` branches  
- **Purpose:** Performance optimization or profiling branches
- **Naming:** `perf/profiling-0021`, `perf/symmetric-rules-with-performance`
- **Policy:** Include profiling data, performance benchmarks, optimization experiments
- **Linked Issue:** [Issue 0021 — Profiling & Performance Reports](../issues/0021-profiling-performance/)

### `fix/*` branches
- **Purpose:** Bug fixes or targeted corrections
- **Naming:** `fix/github-actions-immich-client-setup`, etc.

### `refactor/*` branches
- **Purpose:** Code structure improvements (not features, not fixes)
- **Naming:** `refactor/config-structure`, etc.

## Related Documentation

- **Versioning & Release Workflow:** See [versioning_workflow.md](./versioning_workflow.md)
  - How versions are tagged
  - When to create tags
  - How develop relates to version management

- **Contributing Guidelines:** See [../CONTRIBUTING.md](../CONTRIBUTING.md)
  - General contribution process
  - PR requirements

- **Git Hygiene Practices:** See [../development.md](../development.md)
  - Commit message conventions
  - When to squash vs. merge

## Branch Maintenance

### When to Delete a Branch
A branch is safe to delete if:
1. **AND** all its commits are already in main (or your current integration branch)
2. **AND** it is NOT one of the special-purpose branches listed above (develop, docs-track, etc.)
3. **AND** the feature/fix it represents has been fully integrated

### When NOT to Delete
Even if a branch appears to contain only old commits:
- **Special-purpose branches** (`docs-track`, `develop`, etc.) should be kept for organizational reasons
- **Named release or milestone branches** may have semantic importance even if their commits are elsewhere

### Checking Branch Status
```bash
# See commits ahead of main for a branch
git log main..origin/feature-name --oneline

# Check if all commits from a branch are in another branch
git log current-branch..another-branch --oneline
# (If empty output, current-branch is fully contained in another-branch)
```

## Current Branch Status (as of 2026-01-17)

**Permanent/Special-purpose:**
- `main` — stable production
- `develop` — integration for features
- `docs-track` — documentation coordination

**Active feature/experiment branches:**
- Various feature/*, perf/*, fix/*, refactor/* branches as needed

**Cleanup candidates:**
- Archive branches should be moved to `archive/` namespace or deleted
- Completed feature branches can be deleted after main integration
