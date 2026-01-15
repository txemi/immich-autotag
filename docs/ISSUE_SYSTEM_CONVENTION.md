# Issue Management System - Convention Summary

## Overview
The project uses a **local-first, documentation-as-code** issue tracking system based on industry standards:
- **ADR (Architecture Decision Records)** - Michael Nygard pattern
- **RFC (Request for Comments)** - Rust/React style workflow
- **Documentation-as-Code** - Markdown in Git, peer-reviewed

**Language policy:** All issue artifacts (readme.md, ai-context.md, technical_design.md, registry entries) must be written in English to keep them searchable and consistent. File names remain kebab-case ASCII.

## Directory Structure
Location: [docs/issues](../issues/)

### Current Issues (16 total)
```
0001-system-initialization/
0002-adopt-local-issue-system/
0003-duplicates-management/
0004-album-detection/
0005-filter-assets/
0006-orphan-albums/
0007-refactor-process-single-asset/
0008-statistics-checkpoint/
0009-config-system-refactor/
0010-core-tagging-feature/
0011-announcement-tracking/
0012-cleanup-redeploy/
0013-git-version-null-in-stats/
0014-jenkins-pipeline-containerization/
0015-github-actions-pypi-publishing/
0016-auto-album-creation/
0017-rules-tag-album-combination/ (NEW)
```

## Folder Structure per Issue
Each issue folder follows this convention:

```
XXXX-slug-name/
├── readme.md          # Master document with requirements, problem, solution
├── ai-context.md      # LLM interaction history, decisions, implementation notes
└── design/            # Technical proposals, diagrams, schemas
    └── technical_design.md (or other files)
```

## File Formats

### 1. readme.md (Master Document)
**YAML Front Matter:**
```yaml
---
status: Proposed|In Progress|Open|Closed|Done|Resolved
version: v1.0
created: 2026-01-14
updated: 2026-01-14
---
```

**Sections:**
- Title: `# XXXX - Short Title`
- Tech Stack: `#Python #Configuration #Rules` etc
- Context: Problem background
- Problem Statement: What's the issue?
- Proposed Solution: How to solve it
- Definition of Done (DoD): Acceptance criteria checklist
- Entry Point: Files/functions to modify
- New Implementation: Files to create
- Related Issues: Cross-references
- References: Links to design docs

### 2. ai-context.md (Development Context)
**Header:**
```
Date: 2026-01-14
Status: Proposed
AI Model: Claude Haiku 4.5
Branch: feature/branch-name
```

**Sections:**
- Problem Analysis
- Key Decisions (with rationale and alternatives)
- Current Implementation Review
- Implementation Plan
- Architecture Considerations
- Example Use Cases
- Challenges & Solutions
- Related Context
- Next Steps

### 3. design/technical_design.md (Technical Details)
**Sections:**
- Overview
- Data Model Changes
- Matching Logic Changes
- Example Scenarios
- Integration Points
- Backward Compatibility
- Testing Strategy
- Performance Considerations
- Edge Cases
- Documentation Requirements
- Rollout Plan

## Registry System
**File:** `registry.md`

**Format:** Markdown table with columns:
- ID: Issue number (XXXX)
- Title: Short descriptive title
- Status: Proposed, In Progress, Open, Closed, Done, Resolved
- Created Date: YYYY-MM-DD
- Version: v0.1, v1.0, etc
- Lead: Link to issue folder

## Naming Convention
**Folder Names:** `XXXX-kebab-case-slug`
- Sequential numbering (0001, 0002, etc)
- Kebab-case slug derived from title
- Example: `0017-rules-tag-album-combination`

## Status Values
- **Proposed**: Documented but not started
- **In Progress**: Currently being implemented
- **Open**: Not yet started, ready when needed
- **Closed**: Abandoned or superseded
- **Done**: Completed and merged
- **Resolved**: Completed and released

## Branch Naming Convention
For implementation branches:
- `feature/rules-tag-album-combination` (based on issue slug)
- `fix/` prefix for bug fixes
- `refactor/` prefix for refactoring tasks
- `docs/` prefix for documentation-only changes

## Usage Workflow (Recommended)
1. Create issue folder: `XXXX-slug-name/`
2. Create readme.md with full specification
3. Create ai-context.md with development notes
4. Create design/ subdirectory with technical details
5. Create feature branch: `feature/slug-name`
6. Update registry.md with new issue entry
7. Implement changes in the branch
8. Update ai-context.md with progress
9. Merge and update status to "Done"

## Key Features
✅ **Sovereign Knowledge**: All tracked in Git, not SaaS platforms
✅ **AI-Optimized**: Designed for language model processing
✅ **Self-Documenting**: Code changes tracked alongside context
✅ **Version Controlled**: Full history preserved
✅ **Industry Standard**: Based on ADR and RFC patterns
✅ **Scalable**: 16+ issues already present, easily expandable

## Integration Points
- Issues can reference each other (e.g., "Related Issues: #0004")
- Code changes link back to issue folders via comments
- Branch names derive from issue slugs
- Registry.md serves as central index

## Examples in Project
- **0016**: Auto-album creation (current feature implementation)
- **0017**: Rules tag+album combination (new feature being planned)
- **0004**: Album detection (foundational logic)
- **0010**: Core tagging system (foundational logic)

## AI Agent Instructions
When creating new issues:
1. Use sequential numbering (last=0017, next=0018)
2. Create complete folder structure immediately
3. Write comprehensive readme.md with all sections
4. Document design decisions in ai-context.md
5. Include technical details in design/ folder
6. Update registry.md with status "Proposed"
7. Create feature branch with appropriate name
8. Commit with descriptive message

---
**Summary**: 17 issues tracked, convention well-established, ready for continuous feature development with full context preservation.
