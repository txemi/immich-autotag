# Album Permissions Synchronization Strategy

## Overview

The album permissions system uses **complete synchronization**: the configuration file is the single source of truth for all album permissions.

## Key Principle

> **Only members explicitly listed in the configuration will have access to matching albums.**

Conversely: **Any member NOT in the configuration will be removed.**

## Why Complete Synchronization?

1. **Configuration is Source of Truth**
   - No manual permission adjustments that could become "orphaned"
   - All permissions are documented and reviewable
   - Easy to understand the current state

2. **Consistency**
   - Matches the pattern used throughout immich-autotag (tags, albums, classifications)
   - Prevents accidental stale permissions

3. **Auditability**
   - Every permission change is tied to a configuration change
   - Clear audit trail in modification report

4. **Safety by Default**
   - Phase 1 (dry-run) shows all changes without executing them
   - Users validate before Phase 2 applies permissions

## Implementation Details

### Phase 1: Detection & Logging (Current)

```
For each album:
  1. Match album name against selection rules
  2. Resolve which groups should have access
  3. Resolve which members from those groups
  4. Log results (no API calls)
  5. Record in modification report
```

Result: `ResolvedAlbumPolicy` containing the **desired state**.

### Phase 2: Synchronization (Planned)

```
For each album with matched policy:
  1. Get current members in album (from Immich API)
  2. Compare with resolved policy members
  3. ADDITIONS: Add members not yet in album
     → Record ALBUM_PERMISSION_SHARED event
  4. REMOVALS: Remove members not in resolved policy
     → Record ALBUM_PERMISSION_REMOVED event
  5. Maintain complete sync
```

## Configuration Example

```python
album_permissions=AlbumPermissionsConfig(
    enabled=True,
    user_groups=[
        UserGroup(name="familia", members=["abuelo@ex.com", "madre@ex.com"]),
        UserGroup(name="amigos", members=["juan@ex.com"]),
    ],
    selection_rules=[
        AlbumSelectionRule(name="Familia", keyword="familia", groups=["familia"], access="view"),
        AlbumSelectionRule(name="Amigos", keyword="amigos", groups=["amigos"], access="view"),
    ],
)
```

## Workflow Example

### Initial State
- Config: `familia: ["abuelo@ex.com", "madre@ex.com"]`
- Album "2024-Familia-Vacation": No members
- Album "Random-Photos": No members

### Phase 2 Execution (First Run)
```
✓ Album "2024-Familia-Vacation" → Add abuelo@ex.com, madre@ex.com
  ALBUM_PERMISSION_SHARED (2 events)

✗ Album "Random-Photos" → No match
```

### Configuration Update (Later)
Change config to: `familia: ["madre@ex.com"]` (remove abuelo)

### Phase 2 Execution (Second Run)
```
✓ Album "2024-Familia-Vacation" → Remove abuelo@ex.com
  ALBUM_PERMISSION_REMOVED (1 event)
✓ Album "2024-Familia-Vacation" → madre@ex.com already has access
  No change needed
```

## Important Notes

### Admin Users
Admin/operator users should **NOT be included in member lists**:
- They could accidentally remove their own access
- Better to handle admin access separately via Immich permissions

Example:
```python
# ✗ WRONG - Don't do this
user_groups=[
    UserGroup(name="family", members=["admin@ex.com", "mother@ex.com"])
]

# ✓ CORRECT - Keep admin separate
user_groups=[
    UserGroup(name="family", members=["mother@ex.com", "uncle@ex.com"])
]
# Admin stays as system owner via Immich settings
```

### Validation (Phase 1 Dry-Run)

Always validate Phase 1 output before enabling Phase 2:

```bash
# Run with Phase 1 (dry-run enabled)
python3 main.py

# Check logs: What would be shared?
# Review modification_report.txt

# Once satisfied, enable Phase 2 in code
python3 main.py  # Now with Phase 2 enabled - will actually sync permissions
```

## Modification Report Events

Track synchronization with these events:

**Phase 1:**
- `ALBUM_PERMISSION_RULE_MATCHED` - Album matched a selection rule
- `ALBUM_PERMISSION_GROUPS_RESOLVED` - Groups and members determined
- `ALBUM_PERMISSION_NO_MATCH` - Album didn't match any rule

**Phase 2:**
- `ALBUM_PERMISSION_SHARED` - User added to album
- `ALBUM_PERMISSION_REMOVED` - User removed from album (sync)
- `ALBUM_PERMISSION_SHARE_FAILED` - Error during sharing

## Configuration Changes at Runtime

You can safely modify the configuration between runs:

| Action | Effect on Phase 2 |
|--------|------------------|
| Add member to group | Will be added to matching albums |
| Remove member from group | Will be removed from matching albums |
| Change keyword | Albums matching old keyword lose access; new keyword matches gain access |
| Disable rule | All members in that rule lose access to those albums |
| Disable feature | All shared albums keep current state (no sync) |

**After any config change, always validate Phase 1 output first.**

## Best Practices

1. **Start Small**: Begin with one group and one rule
2. **Use Phase 1**: Always review dry-run before Phase 2
3. **Version Control**: Keep config in git with clear comments
4. **Naming**: Use clear group/rule names for audit trail
5. **Regular Reviews**: Periodically review who has access to what
6. **Test Changes**: When updating config, validate Phase 1 first

## Rollback

If something goes wrong:

1. **Disable feature**: Set `album_permissions.enabled = False`
2. **No automatic cleanup**: Immich keeps existing permissions until removed manually
3. **Re-enable with caution**: Once fixed, re-run Phase 1 to validate

To remove all permission-based sharing:
- Set config `enabled = False`
- Manually review and remove members from albums in Immich UI
- (Future: Could add cleanup command)
