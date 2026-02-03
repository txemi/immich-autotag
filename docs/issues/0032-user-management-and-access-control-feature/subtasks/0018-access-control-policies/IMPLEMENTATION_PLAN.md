# Album Permission Groups - Implementation Plan (0018)

## Branch Structure
```
feat/album-permission-groups (current)
├── Contains: Operational spec documentation
├── Fixes/optimizations: Go to perf/symmetric-rules-with-performance
└── Ready for: Implementation starting next
```

## What We're Building (Based on Your Requirements)

### The Problem
- You have 326 albums in Immich
- Want to quickly share albums with family members based on album names
- Currently names like: "2024-Family-Christmas", "2024-Friends-Meeting", "2024-Work"
- No native Immich user groups

### The Solution (3-Phase Approach)

#### **PHASE 1: Detection & Logging (Safe, Dry-Run)**
When you run the app with `--album-permissions` flag:

1. **Define groups in config**:
```python
user_groups = {
    "family": ["grandfather@...", "mother@...", "brother@..."],
    "amigos": ["juan@...", "maria@..."],
    "trabajo": ["jefe@...", "colega1@..."],
}
```

2. **Define rules in config**:
```python
album_selection_rules = [
    {"keyword": "familia", "groups": ["familia"], "access": "view"},
    {"keyword": "amigos", "groups": ["amigos"], "access": "view"},
    {"keyword": "trabajo", "groups": ["trabajo"], "access": "edit"},
]
```

3. **App does**:
   - Parse album name: `"2024-Familia-Navidad"` → words: `["2024", "Familia", "Navidad"]`
   - Match keyword: `"familia"` found (case-insensitive) ✓
   - Resolve: Album matches rule → group "familia" → 3 members
   - **LOG**: "Album would be shared with: abuelo@, madre@, hermano@"
   - **REPORT**: Add event `ALBUM_PERMISSION_MATCHED_RULE`

4. **You verify**:
   - Check console output: "Correct albums matched?"
   - Review modification_report: "Right groups assigned?"
   - If wrong: Adjust keywords in config → try again

**Cost**: Zero API calls, completely safe

---

#### **PHASE 2: Actual Sharing (When You Approve)**
When you're confident and enable with flag:

1. App does same parsing + matching
2. **THEN**: Makes Immich API call for each member:
   - `POST /albums/{album_id}/users`
   - Add user with specified access level (view/edit/admin)
3. **LOG**: "Successfully shared album with abuelo@"
4. **REPORT**: Event `ALBUM_PERMISSION_SHARED`

**Cost**: One API call per (album, member) pair

---

#### **PHASE 3: Advanced (Future)**
- Support YAML in album description (optional, more control)
- Multiple groups per album
- Different access levels per member

---

## How Keyword Matching Works

**Album name**: `"2024-Family-Vacation-Summer"`  
**Separators**: space, hyphen, underscore, dot  
**Split**: `["2024", "Family", "Vacation", "Summer"]`  
**Rules**:
- If config has keyword `"family"` → **MATCH** (case-insensitive)
- If config has keyword `"vacation"` → **MATCH**
- If config has keyword `"summer"` → **MATCH**
- If config has keyword `"trabajo"` → **NO MATCH**

**Result**: Album could match multiple rules and accumulate all groups

---

## Files to Create/Modify

### Config Models (`config/models.py`)
```python
class UserGroup:
    name: str
    members: List[str]  # emails

class AlbumSelectionRule:
    name: str
    keyword: str
    groups: List[str]
    access: str  # "view", "edit", "admin"
```

### New Module (`albums/album_policy_resolver.py`)
```python
def resolve_album_policy(album_wrapper, config) -> ResolvedPolicy:
    # 1. Get album name
    # 2. Split by separators
    # 3. Match keywords against rules
    # 4. Accumulate groups + members
    # 5. Return policy object
```

### Integration (`entrypoint.py`)
```python
if args.album_permissions:
    for album_wrapper in albums:
        policy = resolve_album_policy(album_wrapper, config)
        if policy:
            log_policy(policy)  # Phase 1
            # share_album(album_wrapper, policy)  # Phase 2
            report.record_event(policy)
```

### Reporting (`report/modification_report.py`)
```python
class ModificationKind:
    ALBUM_PERMISSION_MATCHED_RULE = "..."
    ALBUM_PERMISSION_SHARED = "..."
```

---

## Next Steps

### Before Implementation
1. ✅ **Review this plan** - Does it match what you want?
2. ✅ **Confirm keyword matching logic** - OK with case-insensitive word splitting?
3. ✅ **Confirm config format** - OK with Python dict format?
4. ✅ **Confirm Phase 1 is dry-run only** - Safety first?

### Implementation Roadmap
1. Update config models (`UserGroup`, `AlbumSelectionRule`)
2. Create album_policy_resolver.py
3. Add example config in user_config_template.py
4. Integrate into entrypoint.py
5. Add modification report events
6. Test with dry-run on real config
7. Deploy to Jenkins (dry-run first!)
8. User validates → Enable Phase 2 (actual sharing)

---

## Safety Features

✅ **Phase 1 dry-run**: See what would happen before API calls  
✅ **Detailed logging**: Know exactly which albums matched which rules  
✅ **Modification report**: Audit trail of all decisions  
✅ **Config-driven**: Change behavior without code changes  
✅ **CLI flag**: Enable feature explicitly, disabled by default  

---

## Questions for Clarification

1. ❓ Keyword matching: Should we support **regex** or just simple substring matching?
   - → Plan: Simple substring (case-insensitive) for now
   
2. ❓ Multiple groups per album: Should we accumulate all matching groups?
   - → Plan: YES, collect all matches
   
3. ❓ Access levels: Always "view" for now?
   - → Plan: Configurable per rule (view/edit/admin)
   
4. ❓ Non-matching albums: Should we log them?
   - → Plan: Optional (configurable to avoid noise)

---

## Current Status

- ✅ Branch: `feat/album-permission-groups` created
- ✅ Documentation: Operational spec written
- ✅ Plan: Ready for review and approval
- ⏳ Code: Ready to implement after approval

**Awaiting**: Your confirmation that this matches your requirements!
