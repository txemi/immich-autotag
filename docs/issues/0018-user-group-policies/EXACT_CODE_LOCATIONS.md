# EXACT Code Location for Permissions

## SET PERMISSIONS (When an album is created)

### File: `immich_autotag/albums/album_collection_wrapper.py`

```
LINE   CODE
────────────────────────────────────────────────────────────────
 92    from immich_client.api.albums import add_users_to_album, ← HERE it is imported
 92    create_album                                              the function to SET

 99    def find_or_create_album(                                ← FUNCTION that SETS permissions
 99        self, ...)

 113   add_users_to_album.sync(                                ← HERE is where it is SET
       id=album.id,                                             the (REAL) permission
       client=client,
       body=AddUsersDto(
           album_users=[
               AlbumUserAddDto(
                   user_id=user_id,
                   role=AlbumUserRole.EDITOR    ← EDITOR = read + edit
               )
           ]
       ),
    )
```

**What does it do?**
1. Creates a new album
2. Gets the current user ID
3. Calls `add_users_to_album.sync()` 
4. Adds the user as EDITOR

**When is it executed?**
- When creating a new album in Immich

---

## REMOVE PERMISSIONS (DOES NOT EXIST YET)

### Should go in: `immich_autotag/permissions/` (Phase 2)

**Future implementation would be:**

```python
# immich_autotag/permissions/album_permission_executor.py (NEW)

from immich_client.api.albums import remove_user_from_album

def sync_album_permissions(client, album, resolved_policy):
    """Synchronizes full album permissions."""
    
    # 1. Get current users
    current_users = get_album_members(client, album.id)  # API call
    
    # 2. Compare
    to_add = set(resolved_policy.members) - set(current_users)
    to_remove = set(current_users) - set(resolved_policy.members)
    
    # 3. ADD new ones
    for user_email in to_add:
        add_users_to_album.sync(                         ← ALREADY EXISTS
            id=album.id,
            client=client,
            body=AddUsersDto(
                album_users=[AlbumUserAddDto(...)]
            )
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_SHARED
        )
    
    # 4. REMOVE old ones  ← NEEDS TO BE IMPLEMENTED
    for user_id in to_remove:
        remove_user_from_album.sync(                     ← DOES NOT EXIST YET
            id=album.id,
            user_id=user_id,
            client=client
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_REMOVED
        )
```

---

## CURRENT FLOW (Phase 1)

### File: `immich_autotag/entrypoint.py`

```
LINE   CODE
────────────────────────────────────────────────────────────────
  32   def _process_album_permissions(                  ← Phase 1 FUNCTION
  32       user_config,
  32       context: ImmichContext
  32   ) -> None:

  56   log(
  56       "[ALBUM_PERMISSIONS] Starting Phase 1..."    ← LOG: Starting
  56   )

  62   albums_collection = context.albums_collection    ← Reads albums
  64   user_groups_dict = {}                           ← Build lookup dict
  65   if album_perms_config.user_groups:
  66       for group in album_perms_config.user_groups:
  67           user_groups_dict[group.name] = group

  73   for album in albums_collection.values():         ← LOOP: each album
  74       resolved_policy = resolve_album_policy(      ← RESOLVE policy
  74           album_name=album.album_name,
  74           album_id=album.id,
  74           user_groups=user_groups_dict,
  74           selection_rules=album_perms_config.selection_rules
  74       )

  76   if resolved_policy.has_match:                     ← Did it match?
  77       matched_count += 1
  78       log(...)                                      ← LOG: match
  86       report.add_album_permission_modification(    ← REGISTERS event
  86           kind=ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
  86           ...
  86       )

  107  log(                                              ← LOG: final summary
  107      f"[ALBUM_PERMISSIONS] Summary: {matched_count}..."
  107  )
```

**What does Phase 1 do?**
- Only READS the configuration
- Only RESOLVES which users should have access
- Only REGISTERS in the report
- ❌ NO real changes made in Immich

---

## WHERE POLICY RESOLUTION IS LOCATED

### File: `immich_autotag/albums/album_policy_resolver.py`

```
LINE   CODE
────────────────────────────────────────────────────────────────
  96   def resolve_album_policy(                        ← FUNCTION: resolve
  96       album_name: str,
  96       album_id: str,
  96       user_groups: Dict[str, UserGroup],
  96       selection_rules: List[AlbumSelectionRule],
  96   ) -> ResolvedAlbumPolicy:

  122  for rule in selection_rules:                     ← LOOP: each rule
  123      if _match_keyword_in_album(album_name, rule.keyword):
  124          matched_rules_names.append(rule.name)
  125          all_groups.extend(rule.groups)           ← Accumulates groups

  130  for group_name in all_groups_unique:             ← LOOP: each group
  131      if group_name in user_groups:
  132          group = user_groups[group_name]
  133          all_members.extend(group.members)        ← Accumulates members

  137  return ResolvedAlbumPolicy(                       ← RETURNS result
  137      album_name=album_name,
  137      matched_rules=matched_rules_names,
  137      groups=all_groups_unique,
  137      members=all_members_unique,                  ← THESE are the ones who
  137      access_level=access_level,                     should have access
  137  )
```

**What does it return?**
```
ResolvedAlbumPolicy(
    album_name="2024-Familia-Vacation",
    album_id="abc123",
    matched_rules=["Share Familia albums"],
    groups=["familia"],
    members=["abuelo@ex.com", "madre@ex.com"],    ← THESE must have access
    access_level="view",
    has_match=True
)
```

---

## WHERE CHANGES ARE REGISTERED

### File: `immich_autotag/report/modification_report.py`

```
LINE   CODE
────────────────────────────────────────────────────────────────
 268   def add_album_permission_modification(           ← METHOD to register
 268       self,
 268       kind: ModificationKind,
 268       album: Optional[AlbumResponseWrapper] = None,
 268       matched_rules: Optional[list[str]] = None,
 268       groups: Optional[list[str]] = None,
 268       members: Optional[list[str]] = None,
 268       access_level: Optional[str] = None,
 268       extra: Optional[dict] = None,
 268   ) -> None:

 291   assert kind in {                                 ← VALIDATES that it is
 291       ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
 291       ModificationKind.ALBUM_PERMISSION_GROUPS_RESOLVED,
 291       ModificationKind.ALBUM_PERMISSION_NO_MATCH,
 291       ModificationKind.ALBUM_PERMISSION_SHARED,    ← when it is SET
 291       ModificationKind.ALBUM_PERMISSION_REMOVED,   ← when it is REMOVED ✨ NEW
 291       ModificationKind.ALBUM_PERMISSION_SHARE_FAILED,
 291   }

 311   self.add_modification(                           ← REGISTERS in report
 311       kind=kind,
 311       album=album,
 311       extra=extra,  # With members, groups, etc.
 311   )
```

**What does it register?**
- Each permission decision
- Which album it affects
- Which users, groups, and rules were involved
- It will be saved in `modification_report.txt`

---

## AVAILABLE EVENTS

### File: `immich_autotag/tags/modification_kind.py`

```
LINE   CODE
────────────────────────────────────────────────────────────────
  46   ALBUM_PERMISSION_RULE_MATCHED = auto()           ← Album matched
  47   ALBUM_PERMISSION_GROUPS_RESOLVED = auto()        ← Groups resolved
  48   ALBUM_PERMISSION_NO_MATCH = auto()               ← No match
  49   
  50   # Phase 2: actual sharing
  51   ALBUM_PERMISSION_SHARED = auto()                  ← User ADDED ✅
  52   ALBUM_PERMISSION_REMOVED = auto()                 ← User REMOVED ✅ NEW
  53   ALBUM_PERMISSION_SHARE_FAILED = auto()            ← Error adding
```

---

## SUMMARY: WHERE EVERYTHING HAPPENS

| WHAT | WHERE | LINE | STATUS |
|-----|-------|-------|--------|
| **Policy resolution** | `album_policy_resolver.py` | 96-137 | ✅ |
| **Get current members** | Immich API | — | ❌ TODO |
| **SET new permissions** | `album_collection_wrapper.py` | 113 | ✅ |
| **REMOVE old permissions** | Immich API | — | ❌ TODO |
| **Register in report** | `modification_report.py` | 268 | ✅ |
| **Phase 1** (detect, doing nothing) | `entrypoint.py` | 32 | ✅ |
| **Phase 2** (execute real changes) | — | — | ❌ TODO |

---

## NEXT STEP: PHASE 2

To implement Phase 2, we will need:

1. **Obtain current album users**
   - Use API: `get_album_users()` from Immich client
   - Extract IDs/emails of who has access now

2. **Synchronization function**
   ```python
   # New module: immich_autotag/permissions/album_permission_executor.py
   
   def sync_album_permissions(client, album, resolved_policy):
       current = get_album_users(client, album.id)  # Get current
       to_add = resolved_policy.members - current    # Calculate diff
       to_remove = current - resolved_policy.members
       
       # Add new (use add_users_to_album - ALREADY EXISTS)
       # Remove old (use remove_user_from_album - IMPLEMENT)
   ```

3. **Call from entrypoint**
   ```python
   # immich_autotag/entrypoint.py
   _execute_album_permissions(manager.config, context)  # New function
   ```

Do you want me to continue with Phase 2? 🚀
