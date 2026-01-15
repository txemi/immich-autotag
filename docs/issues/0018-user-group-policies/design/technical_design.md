# Technical Design - 0018 User Groups and Album Policies

## Overview
Define logical groups and policies in config; albums declare which group/policy they belong to via description metadata (YAML) or keyword in the name. Resolve group -> users/actions and record anomalies.

## Data Model (config)
- `UserGroup`:
  - `name: str`
  - `members: list[str]` (emails/ids)
- `GroupPolicy`:
  - `group: str`
  - `access: str` (view|edit|admin)
  - `tags?: list[str]` (optional tags to apply)
- In `UserConfig`:
  - `user_groups: list[UserGroup]`
  - `group_policies: list[GroupPolicy]`

## Album Metadata Format
- Preferred: YAML in album description
```
autotag:
  group: familia
  access: view
  tags:
    - autotag_output_shared_familia
```
- Fallback (less robust): keyword in name, e.g., `[group:familia] Album 2024`

## Parsing Flow
1. Read album description; extract YAML block under key `autotag` (ignore if missing or invalid).
2. If no valid YAML, search keyword `[group:<name>]` in name.
3. Resolve group -> policy -> members/actions.
4. Return `ResolvedPolicy` with group, access, members, tags.

## Integration Points
- Albums module: helper `resolve_album_policy(album_wrapper)`.
- Reporting: if metadata missing or conflict (nonexistent group, invalid YAML, multiple groups), record in `modification_report` with a `ModificationKind` such as `ALBUM_POLICY_WARNING`.

## Error Handling / Reporting
- Invalid YAML: log WARN/FOCUS and record in report (do not stop flow).
- Group not defined in config: record in report.
- No metadata: record optional notice (configurable) or stay silent to avoid noise.

## Testing
- Album with valid YAML -> policy resolved.
- Album with keyword in name -> policy resolved.
- Album without metadata -> notice recorded.
- Corrupt YAML -> notice and fallback to keyword if present.
- Nonexistent group -> notice recorded.

