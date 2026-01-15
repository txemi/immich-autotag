# 0018 - AI Development Context

**Date**: 2026-01-15
**Status**: Proposed
**AI Model**: GPT-5.1-Codex-Max
**Branch**: `feature/rules-tag-album-combination`

## Problem Analysis
Immich has no native groups. We want logical groups in config and to map them to album policies. The album should declare its policy via metadata (ideally YAML in description), with optional keyword fallback in the name.

## Key Decisions
- Use **YAML in album description** under `autotag:` to declare `group` and possible overrides (e.g., `access: view|edit`).
- Keep **name keyword fallback** for quick compatibility (e.g., `[group:family]`).
- Centralize group catalog in config (`user_groups` + `group_policies`).
- Log missing/conflicts in `modification_report`.

## Current Implementation Review
- Config models lack groups and policies.
- No album metadata parser nor policy resolution exists yet.
- Reporting exists (modification_report) and can record findings.

## Plan
1) Config models: `UserGroup`, `GroupPolicy`, maps in `UserConfig`.
2) Album metadata parser: read YAML in description (`autotag:`), fallback keyword in name.
3) Resolve policy: album -> group -> actions/users.
4) Report cases without metadata or conflicts (multiple groups, invalid YAML).
5) Update templates and docs.

## Risks / Edge Cases
- Descriptions missing or corrupted YAML: log warning and fallback.
- Album renames break keyword; hence YAML is preferred.
- Users not present in Immich: report.

## Next Steps
- Design models and metadata format (technical_design.md).
- Implement parser + resolver.
- Add examples to user_config_template.
