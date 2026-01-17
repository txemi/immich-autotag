# Feature Analysis: Remove Assets from Auto-Generated Temporary Albums

**Date:** 17 de Enero de 2026  
**Status:** Analysis (Ready for Implementation)  
**Parent Issue:** 0016 - Auto Album Creation from Date  
**Proposed:** As subtask of 0016

---

## Problem Statement

**Current Behavior:**
- Assets without classification are assigned to temporary auto-generated albums: `YYYY-MM-DD-autotag-temp-unclassified`
- **Only ADD operation exists** - once assigned, assets stay in these temporary albums
- Race conditions from parallel builds can result in: asset has legitimate classification + still in temporary album

**Example Scenario:**
1. Build A starts processing asset X → no classification found → assigned to `2026-01-17-autotag-temp-unclassified`
2. Build B concurrently updates classification rules → now asset X matches a rule → assigned to legitimate album `Family`
3. **Result:** Asset X in BOTH albums
   - ✅ Legitimate: `Family` (correct)
   - ❌ Temporary: `2026-01-17-autotag-temp-unclassified` (now unnecessary)

**Impact:**
- Temporary albums pollute Immich with orphaned assets
- No way to clean up without manual user intervention
- Bad user experience (confusing duplicate assignments)

---

## Proposed Solution

**When to Remove:**
- During asset processing, after classification rules are applied
- IF asset has legitimate classification album
- AND asset is currently in a temporary autotag album (`autotag-temp-*`)
- THEN remove asset from temporary album

**Code Entry Point:**
- Location: `immich_autotag/assets/albums/analyze_and_assign_album.py`
- After classification rules matched (not in unclassified path)
- Add logic to remove from temporary albums **before** returning

**Why This Works for Race Conditions:**
- No locking needed - idempotent operation
- Each asset is checked independently
- If multiple builds run in parallel:
  - Build A: removes from temp album
  - Build B: tries to remove but asset already gone (no error, safe)
  - Result: Asset eventually clean in one album only

---

## Implementation Plan

### Phase 1: Add Remove Capability

**New Method:** `AlbumResponseWrapper.remove_asset()`

```python
# File: immich_autotag/albums/album_response_wrapper.py

def remove_asset(
    self,
    asset_wrapper: "AssetResponseWrapper",
    client: ImmichClient,
    tag_mod_report: "ModificationReport" = None,
) -> None:
    """
    Removes the asset from the album using the API.
    
    - Uses immich_client.api.albums.remove_assets_from_album
    - Validates asset was removed
    - Logs to modification report
    - Safe if asset already removed (no error)
    """
```

**Implementation Details:**
- Mirror existing `add_asset()` pattern
- Use Immich API: `remove_assets_from_album(id, client, body=BulkIdsDto(ids=[...]))`
- Add ModificationKind: `REMOVE_ASSET_FROM_ALBUM`
- Update cached `asset_ids` set after removal

---

### Phase 2: Create Helper Function

**New Function:** `remove_from_autotag_albums.py`

```python
# File: immich_autotag/assets/albums/remove_from_autotag_albums.py

def remove_asset_from_autotag_temporary_albums(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> list[str]:
    """
    Removes asset from ALL temporary autotag albums (pattern: autotag-temp-*).
    
    Returns: List of album names removed from (for logging)
    
    Logic:
    1. Get all albums asset belongs to
    2. Filter for autotag-temp-* albums
    3. For each temporary album:
       - Remove asset
       - Log removal
       - Update modification report
    4. Return list of removed album names
    """
```

**Key Points:**
- Checks configuration: `remove_asset_from_autotag_temporary_albums` flag (new config option)
- Only removes from AUTOTAG temporary albums (pattern-based)
- Never touches user-created albums (even if named similarly)
- Idempotent (safe for multiple executions)

---

### Phase 3: Integration

**Update:** `analyze_and_assign_album.py`

**Current Flow:**
```
1. Check exclusion tags
2. Apply classification rules
   ├─ If 1+ match: Assign to classification album → RETURN
   └─ If 0 match: Create temporary album → RETURN
```

**New Flow:**
```
1. Check exclusion tags
2. Apply classification rules
   ├─ If 1+ match:
   │  ├─ Assign to classification album
   │  ├─ Remove from temporary autotag albums ← NEW
   │  └─ RETURN
   └─ If 0 match:
      ├─ Create temporary album
      └─ RETURN
```

**Code Location:**
- Add after classification album assignment (before return)
- Call: `remove_asset_from_autotag_temporary_albums(asset_wrapper, tag_mod_report)`

---

## Configuration Changes

**New Config Option:**

```python
# File: immich_autotag/config/user_config_template.py

class AutotagAlbumConfig:
    remove_asset_from_autotag_temporary_albums: bool = True  # Default: enabled
    # Clean up temporary album assignments when asset gets permanent classification
```

**Impact:**
- Conservative: Default ON (automatically clean)
- User can disable if concerned about unintended removals
- Aligns with philosophy of "temporary albums are meant to be temporary"

---

## Functions Modified

| File | Function | Change |
|------|----------|--------|
| `album_response_wrapper.py` | NEW: `remove_asset()` | Add method (mirror of `add_asset()`) |
| `create_album_if_missing_classification.py` | None | No change needed |
| `analyze_and_assign_album.py` | `analyze_and_assign_album()` | Add cleanup logic before return |
| `user_config_template.py` | Class: `AutotagAlbumConfig` | Add new config flag |

**Files to Create:**
- `immich_autotag/assets/albums/remove_from_autotag_albums.py` (new module)

---

## Safety Considerations

### Race Condition Handling
- ✅ Asset already removed by another build? → No error (idempotent)
- ✅ Asset being removed while user viewing? → Immich API handles gracefully
- ✅ User manually removed? → No error, just confirms removal

### Rollback Safety
- Feature can be disabled via config (safe revert)
- ModificationReport tracks all removals (audit trail)
- No album is deleted, only asset membership changed

### Edge Cases
1. **Asset in album with pattern `autotag-temp-*` but user-created:**
   - WON'T remove (must be intentional user creation)
   - Pattern is reserved for system use

2. **Album name collision (e.g., user creates "autotag-temp-memes"):**
   - Won't touch it (users own their album management)
   - System only manages albums it creates

3. **Configuration has typo in pattern:**
   - Safe default: only remove exact pattern matches
   - No pattern wildcard interpretation

---

## Testing Strategy

### Unit Tests
- `test_remove_asset_from_album_single()` - remove from one album
- `test_remove_asset_from_album_idempotent()` - remove twice (no error)
- `test_remove_asset_idempotent_with_network_delay()` - simulate concurrent removes

### Integration Tests
- `test_analyze_and_assign_album_with_cleanup()` - unclassified → classified
- `test_parallel_builds_remove_cleanup()` - 2+ builds processing same asset
- `test_config_flag_disabled()` - verify cleanup doesn't run when config=false

### Smoke Tests
- Run on 240K+ assets test suite
- Verify no removal errors, proper logging
- Check ModificationReport captures all removals

---

## Estimated Effort

| Phase | Task | Estimate |
|-------|------|----------|
| 1 | Add `remove_asset()` method | 1-2h |
| 2 | Create `remove_from_autotag_albums.py` | 1-2h |
| 3 | Integrate into `analyze_and_assign_album.py` | 1h |
| - | Config updates | 30min |
| - | Unit + integration tests | 2-3h |
| - | Documentation update | 1h |
| **Total** | **Full Feature** | **7-10h** |

---

## Next Steps

1. ✅ Analysis complete (THIS DOCUMENT)
2. Create feature branch: `feat/0016-remove-from-autotag-album`
3. Implement Phase 1: `remove_asset()` method
4. Implement Phase 2: Helper function
5. Implement Phase 3: Integration
6. Test with Jenkins builds
7. Create Issue #0016.1 as subtask (formal tracking)

---

## Notes

- **Blocking:** No - can be implemented independently
- **Release:** Post-stabilization (after current test battery passes)
- **Risk:** Low (idempotent, disabled by default if needed, audit trail)
- **Value:** High (improves UX, solves race condition artifacts)

---
