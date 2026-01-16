---
status: In Progress
version: v1.0
created: 2026-01-15
updated: 2026-01-16
---

# 0018 - User Groups and Album Permission Management

## Tech Stack
#Python #Configuration #Rules #Immich #Jenkins #Album-Sharing

## Context
Immich does not provide native user groups, but we need to assign album access automatically via autotag configuration. The practical implementation uses album name keywords (already in use) to trigger permission assignments to predefined user groups.

## Problem Statement
- No native groups in Immich to share/manage access in bulk
- Current config cannot define logical groups or map them to album policies
- With hundreds of albums, manual sharing by name pattern is inefficient
- Need automated, practical system that doesn't require YAML in album descriptions

## Proposed Solution
- Define `user_groups` in config with members
- Define `album_selection_rules` that match keywords in album names
- Automatically map albums to groups based on keywords (case-insensitive word matching)
- **Phase 1 (Dry-run)**: Log matches and record in report without API calls
- **Phase 2 (Sharing)**: Enable actual sharing via Immich API

## Key Features
- **Keyword-based**: Album names already follow naming convention with keywords (e.g., "2024-Familia-Navidad")
- **Separator-aware**: Split album name by space, hyphen, underscore, dot to extract words
- **Case-insensitive**: "familia" matches "Familia" in album name
- **Multiple rules**: Album can match multiple rules and accumulate group memberships
- **Safe by default**: Phase 1 is dry-run only; user validates before enabling sharing
- **Well-reported**: Detailed logging in modification_report for audit trail

## Design Documents
- [Operational Specification](design/OPERATIONAL_SPEC.md) - **START HERE**: User requirements and implementation details
- [Technical Design](design/technical_design.md) - Lower-level implementation patterns

## Definition of Done (DoD)
- Config supports `user_groups` and `album_selection_rules` blocks
- Album name parser splits by separators and matches keywords
- Policy resolver returns group/users/access level
- Phase 1: Console logging + modification_report entries (no API calls)
- CLI flag `--album-permissions` enables the feature (dry-run by default)
- Docs updated with examples in config template
- Unit + integration tests for parsing and resolution
- Manual validation on real config before Phase 2

## Entry Points
- `immich_autotag/config/models.py` (UserGroup, AlbumSelectionRule models)
- `immich_autotag/config/user_config_template.py` (examples)
- `immich_autotag/albums/album_policy_resolver.py` (NEW: policy resolution logic)
- `immich_autotag/entrypoint.py` (integration point)
- `immich_autotag/report/modification_report.py` (new event kinds)

## Implementation Phases
1. **Phase 1 (Current)**: Detection & logging (dry-run, no API calls)
2. **Phase 2 (Future)**: Actual sharing via API calls
3. **Phase 3 (Future)**: YAML in album description + multiple groups per album

## Related Issues
- #0009 Configuration System Refactor (config models)
- #0017 Tag+Album Rules (unified config approach)
- #0021 Profiling & Performance (batch operation optimization)

## References
- Immich API: `/albums/{id}/users` endpoint for sharing
- Album name convention: Already in use (e.g., "YYYY-Keyword-Description")
- YAML album metadata convention (similar to front-matter)
