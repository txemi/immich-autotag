---
status: Proposed
version: v1.0
created: 2026-01-15
updated: 2026-01-15
---

# 0018 - User Groups and Album Policies

## Tech Stack
#Python #Configuration #Rules #Immich #Jenkins

## Context
Immich does not provide native user groups, but we need to assign access/policies automatically via autotag configuration. We also want to read per-album metadata (name/description) to decide which policy to apply.

## Problem Statement
- No native groups in Immich to share/manage access in bulk.
- Current config cannot define logical groups or map them to album policies.
- Unclear where to store album policy: encoded in name (keywords) or in description (YAML).

## Proposed Solution
- Define `user_groups` in config (YAML/Python) with members and per-group policies.
- Allow annotating albums with metadata (preferred: YAML in description; fallback: keyword in name).
- Resolve policy by combining album metadata with the group catalog in config.
- Record in reports the albums missing metadata or with conflicts.

## Definition of Done (DoD)
- Config supports `user_groups` and `group_policies` blocks, documented with examples.
- Album metadata parser: YAML in description (root `autotag:`) plus keyword fallback in name.
- Policy resolution returns group/users/expected actions.
- `modification_report` records cases without metadata or with conflicts.
- Docs updated (config README + this issue) with format and examples.

## Entry Points
- `immich_autotag/config/models.py` (new user_groups / policies models)
- `immich_autotag/config/user_config_template.*` (examples)
- `immich_autotag/assets/albums/*` (album metadata reading)
- `immich_autotag/report/modification_report.py` (logging missing/conflicts)

## New Implementation
- Add `UserGroup` and `GroupPolicy` models in config.
- Add album metadata parser: read description (YAML) or keywords in name.
- Resolve album -> group -> policy and expose helper.

## Related Issues
- 0014 Jenkins pipeline (logs/policies artifacts)
- 0017 Tag+album rules (unified config)

## References
- Immich API sharing (no native groups)
- YAML album metadata convention (similar to front-matter)
