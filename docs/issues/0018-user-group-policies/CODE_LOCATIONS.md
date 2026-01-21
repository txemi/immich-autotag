
# Location of Granting/Revoking Permissions in the Code

## Visual Summary

```

┌────────────────────────────────────────────────────────────────────┐
│                    HOW PERMISSIONS WORK                            │
└────────────────────────────────────────────────────────────────────┘

CURRENTLY (ALREADY EXISTS):
    ✓ GRANT permissions
    ✗ REVOKE permissions (NOT IMPLEMENTED YET)

```

---


## 1. GRANT PERMISSIONS - ALREADY EXISTS ✓


### Location: `immich_autotag/albums/album_collection_wrapper.py`


**Line 92-113**: Function `find_or_create_album()`

```python
# Line 92: Imports the API function
from immich_client.api.albums import add_users_to_album, create_album

# Line 113: Calls the function to ADD users
add_users_to_album.sync(
    id=album.id,
    client=client,
    body=AddUsersDto(
        album_users=[
            AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)
        ]
    ),
)
```


**When is it executed?**
- When a new album is created
- The owner is added as EDITOR


**What matters here?**
- `add_users_to_album`: Immich API function that **ADDS** users to an album
- `AddUsersDto`: DTO with a list of users and roles

---


## 2. REVOKE PERMISSIONS - NOT IMPLEMENTED YET ❌


**Where should it go?**

To keep consistency with the project structure, it should go in:
1. `immich_autotag/albums/album_collection_wrapper.py` (new method)
    - Or better, in a new package `immich_autotag/permissions/`

**How would it be implemented?**

```python
# New function in album_collection_wrapper.py or permissions/

def remove_user_from_album(client, album_id: str, user_id: str):
    """Removes a user from an album."""
    from immich_client.api.albums import remove_user_from_album as api_remove
    
    api_remove.sync(
        id=album_id,
        user_id=user_id,
        client=client
    )
```

---

## 3. CURRENT FLOW (Phase 1 - Dry-run)

```
┌─────────────────────────────────────────────────┐
│  immich_autotag/entrypoint.py                   │
│  _process_album_permissions()                   │  ← Detection only
│                                                 │
│  - Reads config                                 │
│  - Resolves policies (resolver)                 │
│  - Logs results                                 │
│  - Registers in modification_report             │
│                                                 │
│  ❌ DOES NOT MAKE REAL API CALLS                │
└─────────────────────────────────────────────────┘
```

---

## 4. PHASE 2 FLOW (PLANNED - Synchronization)

```
┌──────────────────────────────────────────────────────────┐
│  immich_autotag/entrypoint.py                            │
│  _execute_album_permissions() ← NEW PHASE 2 FUNCTION     │
│                                                          │
│  For each album:                                         │
│    ├─ Get resolved policy (resolver)                     │
│    │                                                     │
│    ├─ Get CURRENT members (API)                          │
│    │  └─ album.get_user_shares()  ← NOT IMPLEMENTED      │
│    │                                                     │
│    ├─ COMPARE:                                           │
│    │  ├─ Members to ADD = config - current               │
│    │  └─ Members to REMOVE = current - config            │
│    │                                                     │
│    ├─ ADD: add_users_to_album.sync() ✓ EXISTS            │
│    │  └─ Report: ALBUM_PERMISSION_SHARED                 │
│    │                                                     │
│    └─ REMOVE: remove_user_from_album.sync() ❌ TODO      │
│       └─ Report: ALBUM_PERMISSION_REMOVED                │
└──────────────────────────────────────────────────────────┘
```

---

## 5. WHERE IMMICH API IS LOCATED

**File**: Inside `immich-client/` (API client)

```
immich-client/
├── immich_client/
│   └── api/
│       └── albums.py          ← Here are the functions
```

**Available functions in `albums.py`:**
- ✅ `add_users_to_album()` - SET users
- ❌ `remove_user_from_album()` - REMOVE users (needs checking if it exists)
- ✅ `get_album_users()` or similar - GET current users

---

## 6. CURRENT CODE USING PERMISSIONS

### Create Album + Set Permissions
**File**: `immich_autotag/albums/album_collection_wrapper.py:92-113`

```python
from immich_client.api.albums import add_users_to_album, create_album

album = create_album.sync(client=client, body=CreateAlbumDto(...))
add_users_to_album.sync(
    id=album.id,
    client=client,
    body=AddUsersDto(
        album_users=[AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)]
    ),
)
```

**Result**: ✅ User added as EDITOR to the album

---

## 7. PENDING TASKS FOR PHASE 2

```
REQUIRED TO IMPLEMENT:

1. ✓ Event ALBUM_PERMISSION_REMOVED - ALREADY ADDED
2. ✓ Synchronization documentation - ALREADY DONE
3. ❌ Function remove_user_from_album() - TODO
4. ❌ Get current user list in album - TODO
5. ❌ Sync logic in entrypoint - TODO
6. ❌ Sync tests - TODO
```

---

## 8. COMPLETE MENTAL MAP

```
ENTRY POINT:
  entrypoint.py
  └─ run_main()
     ├─ Phase 1: _process_album_permissions()  ✓ ALREADY EXISTS
     │  ├─ albums/album_policy_resolver.py
     │  │  └─ resolve_album_policy()
     │  └─ report/modification_report.py
     │     └─ add_album_permission_modification()
     │
     └─ Phase 2: _execute_album_permissions()  ❌ TODO
        └─ For each album:
           ├─ resolver: resolve_album_policy()  ✓ EXISTS
           ├─ actual: get_album_users()  ❌ IMPLEMENT
           ├─ sync: add_users_to_album.sync()  ✓ EXISTS
           ├─ sync: remove_user_from_album.sync()  ❌ IMPLEMENT
           └─ report: add_album_permission_modification()  ✓ EXISTS
```

---

## SUMMARY

| Action | Location | Status |
|--------|-----------|--------|
| **SET permissions** | `album_collection_wrapper.py:113` | ✅ ALREADY WORKS |
| **REMOVE permissions** | Does not exist | ❌ TODO Phase 2 |
| **Detect (Phase 1)** | `entrypoint.py:_process_album_permissions()` | ✅ ALREADY EXISTS |
| **Resolve policies** | `albums/album_policy_resolver.py` | ✅ ALREADY EXISTS |
| **Register changes** | `report/modification_report.py` | ✅ ALREADY EXISTS |

---

**In summary:**
- Right now **only setting permissions exists** (when creating albums)
- **Removing permissions does not exist** (will be implemented in Phase 2)
- **Phase 1 only detects** (without making real changes)
- When we implement Phase 2, there will be two new synchronization functions
