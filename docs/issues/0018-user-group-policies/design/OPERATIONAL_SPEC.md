# Operational Specification - Album Permission Groups (0018)

**Author**: txemi  
**Date**: 2026-01-16  
**Status**: Design Review (Ready for Implementation)  
**Branch**: `feat/album-permission-groups`

## Executive Summary

Create a system to automatically assign Immich album access to user groups based on:
1. **Album name keywords** (simple, practical, already in use)
2. **User groups** defined in configuration
3. **Mapping rules** that connect keywords to groups and define permission levels

## Problem Statement

Currently:
- Immich has no native user groups
- Assigning albums to multiple users requires manual sharing
- With hundreds of albums, bulk sharing by name pattern is manual
- Need automated, configurable permission assignment

Example: User has albums like:
- `2024-Familia-Navidad` → should share with "familia" group
- `2024-Amigos-Reunion` → should share with "amigos" group
- `2024-Trabajo-Proyecto` → should share with "trabajo" group

## Proposed Solution

### 1. User Groups Configuration

Define groups in `user_config.py`:

```python
user_groups = {
    "familia": {
        "description": "Familia directa",
        "members": [
            "abuelo@example.com",
            "madre@example.com",
            "hermano@example.com",
        ],
    },
    "amigos": {
        "description": "Círculo de amigos",
        "members": [
            "juan@example.com",
            "maria@example.com",
        ],
    },
    "trabajo": {
        "description": "Equipo de trabajo",
        "members": [
            "jefe@example.com",
            "colega1@example.com",
            "colega2@example.com",
        ],
    },
}
```

### 2. Album Selection Rules

Define rules that select albums by name patterns:

```python
album_selection_rules = [
    {
        "name": "Compartir Familia",
        "keyword": "familia",  # Case-insensitive substring match
        "groups": ["familia"],  # Groups to share with
        "access": "view",  # Permission level: view|edit|admin
    },
    {
        "name": "Compartir Amigos",
        "keyword": "amigos",
        "groups": ["amigos"],
        "access": "view",
    },
    {
        "name": "Compartir Trabajo",
        "keyword": "trabajo",
        "groups": ["trabajo"],
        "access": "edit",  # Trabajo puede editar
    },
]
```

### 3. Album Name Parsing

**Strategy**: Split album name by separators and match keywords.

**Separators**: space, hyphen, underscore, dot

**Example**:
- Album: `2024-Familia-Navidad`
  - Split: `["2024", "Familia", "Navidad"]`
  - Match: `"familia"` (case-insensitive) → Rule matches

- Album: `vacation_friends_2024`
  - Split: `["vacation", "friends", "2024"]`
  - No match → Skip

- Album: `2024_Trabajo_Proyecto_v2`
  - Split: `["2024", "Trabajo", "Proyecto", "v2"]`
  - Match: `"trabajo"` → Rule matches

### 4. Execution Flow

**When**: During album processing (e.g., in `entrypoint.py`)

**For each album**:
1. Get album name
2. Split by separators into words
3. For each selection rule:
   - Check if keyword appears in album words (case-insensitive)
   - If match: extract `groups` list from rule
4. For each matched group:
   - Get members from `user_groups[group_name]`
   - **First iteration (Phase 1)**: Log action, record in report
   - **Future (Phase 2)**: Make API call to share album with each member
5. Record in `modification_report`:
   - Album name
   - Matched rules
   - Groups and members to be shared
   - Success/failure status

### 5. Modification Report Integration

Add new event kinds:

```python
class ModificationKind(Enum):
    # Existing...
    
    # New album permission events
    ALBUM_PERMISSION_SHARED = "album_permission_shared"
    ALBUM_PERMISSION_MATCHED_RULE = "album_permission_matched_rule"
    ALBUM_PERMISSION_NO_MATCH = "album_permission_no_match"  # Optional, for debug
```

Example report entry:

```
Album: 2024-Familia-Navidad
Event: album_permission_matched_rule
Rule: "Compartir Familia"
Keyword: "familia"
Groups: ["familia"]
Members: ["abuelo@example.com", "madre@example.com", "hermano@example.com"]
Access Level: "view"
Status: ready_for_sharing (Phase 1) / shared (Phase 2)
```

### 6. Implementation Phases

**Phase 1 (Current)**: Detection & Logging
- Parse album names, detect matches
- Log to console and report
- NO API calls yet
- User verifies logic is correct before enabling sharing

**Phase 2 (Future)**: Sharing API Calls
- Make actual `add_users_to_album` API calls
- Handle errors (user not found, permission denied)
- Record success/failure in report

**Phase 3 (Future)**: Advanced Features
- Support YAML in album description (like 0018 technical_design suggests)
- Support multiple groups per album
- Support different access levels per member

## Data Structures

### Config Models

```python
# immich_autotag/config/models.py

class UserGroup:
    name: str
    description: Optional[str]
    members: List[str]  # emails or user IDs

class AlbumSelectionRule:
    name: str
    keyword: str  # Single keyword to match in album name
    groups: List[str]  # Group names to share with
    access: Literal["view", "edit", "admin"]

# In UserConfig:
class UserConfig(BaseModel):
    user_groups: Optional[List[UserGroup]] = None
    album_selection_rules: Optional[List[AlbumSelectionRule]] = None
```

### Processing Models

```python
# immich_autotag/albums/album_policy_resolver.py

class ResolvedAlbumPolicy:
    album_name: str
    matched_rules: List[str]  # Rule names
    groups: List[str]  # Group names
    members: List[str]  # Actual emails/IDs
    access_level: Literal["view", "edit", "admin"]
    status: Literal["no_match", "ready", "shared", "error"]
    error_message: Optional[str]

def resolve_album_policy(
    album_wrapper: AlbumResponseWrapper,
    config: UserConfig,
) -> Optional[ResolvedAlbumPolicy]:
    """
    Returns resolved policy or None if no rule matched.
    """
    pass
```

## Entry Points for Implementation

1. **Config parsing**: Update `UserConfig` model in `config/models.py`
2. **Template**: Add examples to `config/user_config_template.py`
3. **Album policy logic**: Create `albums/album_policy_resolver.py`
4. **Integration point**: Call resolver in album processing loop
5. **Reporting**: Add new `ModificationKind` events and log to `modification_report`
6. **CLI/Entrypoint**: Add flag `--album-permissions` to enable feature (Phase 1: dry-run only)

## Testing Strategy

**Unit Tests**:
- Album name parsing (with various separators)
- Keyword matching (case-insensitive, partial)
- Rule resolution (single and multiple matches)

**Integration Tests**:
- Full config parsing with user groups + rules
- Policy resolution on sample albums
- Report generation

**Manual Tests**:
- Dry-run on real config with real albums
- Verify correct groups/members detected
- Enable sharing, verify API calls work

## Success Criteria

✅ Config supports `user_groups` and `album_selection_rules`  
✅ Album names parsed correctly by separators  
✅ Keywords matched case-insensitively  
✅ Groups resolved and members extracted  
✅ Modification report shows all matched albums and groups  
✅ Phase 1: Console output and report (no API calls)  
✅ User can verify before enabling actual sharing  
✅ Documentation with examples in config template  

## Notes

- **Why keywords instead of YAML first?**: Simpler to test, lower friction, user already uses keyword practice
- **Why Phase 1 dry-run?**: Safer; user sees what would happen before making API calls
- **Future YAML support**: Can be added in Phase 3 without breaking keyword matching
- **Separator choice**: Pragmatic; covers most album naming schemes without regex complexity

## Next Steps

1. ✅ Review this spec with user (current)
2. Create issue/task for Phase 1 implementation
3. Implement config models + parser
4. Implement album name splitting + keyword matching
5. Implement policy resolver
6. Add report logging
7. Test with real config
8. Deploy to Jenkins (dry-run)
9. User validates output
10. Plan Phase 2 (actual sharing)
