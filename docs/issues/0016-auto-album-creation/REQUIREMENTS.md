# Issue #001: Auto Album Creation from Date When No Classification Album Found

## Overview
When an asset cannot be assigned to any classification album (according to configured patterns), automatically create a temporary album based on the asset's date if the feature flag is enabled. This provides a fallback mechanism to organize unclassified assets without manual intervention.

## Feature Flag
- **Config Key**: `create_album_from_date_if_missing` (already exists in models)
- **Default Value**: `False` (disabled for safety, can be enabled in user config)
- **Type**: `bool`

## Functional Requirements

### FR-1: Album Name Generation
When creating an album, use the following naming scheme:
```
YYYY-MM-DD-autotag-temp-<category>
```
- **YYYY-MM-DD**: ISO 8601 date extracted from asset (or current date as fallback)
- **autotag-temp**: Static prefix to identify auto-created albums
- **<category>**: Human-readable identifier for the category/reason
  - Examples: "unclassified", "unknown", "pending"

### FR-2: Album Creation Trigger
Album creation should occur when:
1. Asset has been analyzed and no classification album matches (i.e., `decide_album_for_asset()` returns `None` or empty decision)
2. Feature flag `create_album_from_date_if_missing` is `True`
3. Asset does NOT have exclusion tags (e.g., `autotag_input_ignore`, `autotag_input_meme`)

### FR-3: Asset Assignment
After creating the album:
1. Assign the asset to the newly created album
2. Log the assignment with clear messaging
3. Track modification in `ModificationReport` (use existing `CREATE_ALBUM` kind)

### FR-4: Reusability
- If the same date-based album already exists in Immich, reuse it instead of creating a duplicate
- This requires checking existing albums before creating new ones

### FR-5: User Visibility
- Album naming must be clearly recognizable as auto-created (prefix `autotag-temp`)
- Allows users to easily filter, review, rename, or delete these albums
- No destructive actions on user behalf

## Non-Functional Requirements

### NF-1: Code Organization
- **Entry Point Function**: `analyze_and_assign_album.py` → Add conditional logic
- **New Function**: `create_album_if_missing_classification.py` (new file in `albums/` module)
  - Handles the decision to create album and delegates to existing functions
- **Reuse Existing Functions**:
  - `AlbumCollectionWrapper.create_album()` for album creation
  - `_process_album_detection()` for asset-to-album assignment
  
### NF-2: Logging
- Use existing `LogLevel.FOCUS` for significant events
- Provide context: asset name, generated album name, date source

### NF-3: Testing
- Unit tests for album name generation
- Integration test for the full flow (unclassified asset → album creation → assignment)

### NF-4: Configuration Validation
- Warn if flag is enabled but no date can be extracted from asset
- Ensure backward compatibility (disabled by default)

## Implementation Points

### Point 1: Modify `analyze_and_assign_album()`
- After `album_decision.is_unique()` check returns False
- Before logging "no album found" message
- Add: IF (feature enabled AND no classification albums) THEN call `create_album_if_missing_classification()`

### Point 2: New Module `create_album_if_missing_classification.py`
```python
@typechecked
def create_album_if_missing_classification(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> Optional[str]:
    """
    Creates and assigns a temporary album if:
    - Feature flag is enabled
    - Asset has no classification album
    - Asset is not marked for exclusion
    
    Returns: album_name (str) if created/assigned, None otherwise
    """
```

### Point 3: Date Extraction
- Use existing date extraction utilities if available
- Fallback: `asset_wrapper.asset.created_at` or current date
- Format: ISO 8601 (YYYY-MM-DD)

### Point 4: Album Naming Constant
Define in config or constants:
```python
AUTOTAG_TEMP_ALBUM_PREFIX = "autotag-temp"
AUTOTAG_TEMP_ALBUM_CATEGORY = "unclassified"  # or configurable
```

## Edge Cases

1. **No date available**: Log warning, do not create album
2. **Album already exists**: Reuse it (check `AlbumCollectionWrapper` logic)
3. **Excluded assets**: Skip creation (respect `autotag_input_ignore`, etc.)
4. **Duplicate assets**: Apply same album to all duplicates
5. **API failure**: Log error, continue without album (non-blocking)

## Acceptance Criteria

- [ ] Feature flag controls behavior (can be enabled/disabled)
- [ ] Album name follows pattern: `YYYY-MM-DD-autotag-temp-*`
- [ ] Album reused if already exists
- [ ] Asset correctly assigned to created album
- [ ] All modifications logged with FOCUS level
- [ ] Existing unit tests pass
- [ ] New functions have `@typechecked` decorator
- [ ] Code follows project style (imports, naming, structure)
- [ ] Backward compatible (disabled by default)

## References
- Config models: `immich_autotag/config/models.py`
- Current album functions: `immich_autotag/albums/album_collection_wrapper.py`
- Main analysis function: `immich_autotag/assets/albums/analyze_and_assign_album.py`
- Album decision logic: `immich_autotag/assets/albums/decide_album_for_asset.py`
