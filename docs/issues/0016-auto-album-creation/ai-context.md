# AI Development Context: Issue #0016

## Scope
Implement auto album creation feature that generates temporary albums for unclassified assets.

## Key Files to Modify

1. **`immich_autotag/assets/albums/analyze_and_assign_album.py`**
   - Location: After `album_decision.is_unique()` returns False
   - Add conditional call to new function if feature enabled

2. **NEW: `immich_autotag/assets/albums/create_album_if_missing_classification.py`**
   - Main implementation file (see REQUIREMENTS.md for function signature)

## Reusable Functions

| Module | Function | Purpose |
|--------|----------|---------|
| `immich_autotag/albums/album_collection_wrapper.py` | `create_album()` | Create album in Immich |
| `immich_autotag/assets/albums/_process_album_detection.py` | `_process_album_detection()` | Assign asset to album |
| `immich_autotag/config/manager.py` | `ConfigManager.get_instance()` | Access config flags |
| `immich_autotag/assets/asset_response_wrapper.py` | `get_tag_names()` | Get asset tags |

## Config Integration
- Flag already exists: `create_album_from_date_if_missing` in `immich_autotag/config/models.py`
- Default: `False` (disabled)
- User can enable in their config: `config.create_album_from_date_if_missing = True`

## Album Naming Convention
```
YYYY-MM-DD-autotag-temp-unclassified
```
- Prefix `autotag-temp` makes auto-created albums easily recognizable
- Category suffix `unclassified` explains the reason
- Date-based for user organization
- English-friendly for filtering

## Exclusion Logic
Skip auto-album creation if asset has these tags:
- `autotag_input_ignore` (explicitly ignored)
- `autotag_input_meme` (content type, not an event)
- `autotag_input_adult_meme` (content type, not an event)

## Date Extraction Fallback
1. Try: `asset_wrapper.asset.created_at` → ISO format (YYYY-MM-DD)
2. Fallback: Current date
3. Fallback: Log WARN, return None (skip album creation)

## Error Handling
- **Config disabled**: Return None silently
- **Exclusion tags present**: Log DEBUG, skip
- **No date available**: Log WARN, skip
- **Album creation fails**: Log ERROR, non-blocking (continue processing)
- **Assignment fails**: Log ERROR, non-blocking (continue processing)

## Testing Points
1. Album name generation with various dates
2. Exclusion tag logic
3. Date extraction and fallback
4. Album reuse (same date → reuse existing album)
5. Feature flag behavior (enabled/disabled)
6. Integration with existing `_process_album_detection()`

## Backward Compatibility
- Feature disabled by default
- No changes to existing enabled features
- No breaking changes to APIs
- Users must explicitly enable to use

## Performance Considerations
- Album lookup (reuse check) should be O(1) or cached
- Date extraction should be fast
- No API calls if feature disabled

## Related Patterns in Codebase
- Similar album creation in `AlbumCollectionWrapper.create_album()`
- Similar asset assignment in `_process_album_detection()`
- Similar config checks in `ConfigManager.get_instance()`
- Similar logging patterns with `LogLevel.FOCUS`
