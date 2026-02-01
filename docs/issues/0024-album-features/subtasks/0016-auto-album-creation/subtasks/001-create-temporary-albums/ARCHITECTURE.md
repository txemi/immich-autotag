# Architecture: Auto Album Creation Feature

## System Flow

```
analyze_and_assign_album()
    │
    ├─ decide_album_for_asset()
    │   └─ Returns: AlbumDecision (unique, conflict, none)
    │
    ├─ [IF no classification album AND feature enabled]
    │   │
    │   └─ create_album_if_missing_classification()
    │       ├─ Check if asset should be excluded
    │       ├─ Extract date from asset
    │       ├─ Generate album name: YYYY-MM-DD-autotag-temp-unclassified
    │       ├─ Check if album exists (reuse)
    │       ├─ Create album if not exists
    │       ├─ Assign asset to album
    │       └─ Report modification (CREATE_ALBUM)
    │
    └─ [ELSE] Log "no album found"
```

## File Structure

```
immich_autotag/assets/albums/
├── analyze_and_assign_album.py       [MODIFY]
├── decide_album_for_asset.py         [NO CHANGE]
├── _process_album_detection.py       [NO CHANGE - reuse]
└── create_album_if_missing_classification.py  [NEW]
```

## New Function: `create_album_if_missing_classification()`

**File**: `immich_autotag/assets/albums/create_album_if_missing_classification.py`

```python
from __future__ import annotations
from typeguard import typechecked
from datetime import datetime
from typing import Optional
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.logging.utils import log
from immich_autotag.logging.levels import LogLevel
from immich_autotag.config.manager import ConfigManager

# Constants
AUTOTAG_TEMP_ALBUM_PREFIX = "autotag-temp"
AUTOTAG_TEMP_ALBUM_CATEGORY = "unclassified"

@typechecked
def create_album_if_missing_classification(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> Optional[str]:
    """
    Creates and assigns a temporary album for assets with no classification album.
    
    Conditions:
    - Feature flag `create_album_from_date_if_missing` must be enabled
    - Asset must not have exclusion tags (ignore, meme, etc.)
    - Date must be extractable from asset
    
    Returns:
        Album name (str) if created/assigned, None if skipped or failed
    """
    # Check feature flag
    config = ConfigManager.get_instance().config
    if not config.create_album_from_date_if_missing:
        return None
    
    # Check if asset has exclusion tags
    if _has_exclusion_tags(asset_wrapper):
        log(
            f"[ALBUM CREATION] Asset '{asset_wrapper.original_file_name}' "
            f"has exclusion tags, skipping auto-album creation.",
            level=LogLevel.DEBUG
        )
        return None
    
    # Extract date
    album_date = _extract_album_date(asset_wrapper)
    if not album_date:
        log(
            f"[ALBUM CREATION] Could not extract date from asset "
            f"'{asset_wrapper.original_file_name}', skipping auto-album creation.",
            level=LogLevel.WARN
        )
        return None
    
    # Generate album name
    album_name = f"{album_date}-{AUTOTAG_TEMP_ALBUM_PREFIX}-{AUTOTAG_TEMP_ALBUM_CATEGORY}"
    
    # Get or create album
    from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
    albums = AlbumCollectionWrapper(asset_wrapper.context)
    
    # Check if album already exists (reuse)
    existing_album = _find_album_by_name(albums, album_name)
    if existing_album:
        album_id = existing_album
        log(
            f"[ALBUM CREATION] Reusing existing album '{album_name}' for asset "
            f"'{asset_wrapper.original_file_name}'.",
            level=LogLevel.FOCUS
        )
    else:
        # Create new album
        try:
            album_id = albums.create_album(album_name)
            log(
                f"[ALBUM CREATION] Created new album '{album_name}' for asset "
                f"'{asset_wrapper.original_file_name}'.",
                level=LogLevel.FOCUS
            )
        except Exception as e:
            log(
                f"[ALBUM CREATION] Failed to create album '{album_name}': {e}",
                level=LogLevel.ERROR
            )
            return None
    
    # Assign asset to album
    try:
        from immich_autotag.assets.albums._process_album_detection import _process_album_detection
        _process_album_detection(
            asset_wrapper,
            tag_mod_report,
            album_name,
            album_origin="auto-created",
            suppress_album_already_belongs_log=False
        )
        return album_name
    except Exception as e:
        log(
            f"[ALBUM CREATION] Failed to assign asset to album '{album_name}': {e}",
            level=LogLevel.ERROR
        )
        return None


@typechecked
def _has_exclusion_tags(asset_wrapper: AssetResponseWrapper) -> bool:
    """Check if asset has tags that should exclude it from auto-album creation."""
    exclusion_tags = [
        "autotag_input_ignore",
        "autotag_input_meme",
        "autotag_input_adult_meme",
    ]
    asset_tags = asset_wrapper.get_tag_names()
    return any(tag in asset_tags for tag in exclusion_tags)


@typechecked
def _extract_album_date(asset_wrapper: AssetResponseWrapper) -> Optional[str]:
    """Extract date in YYYY-MM-DD format from asset. Fallback to creation date."""
    try:
        # Try to get date from asset creation date (Immich)
        if asset_wrapper.asset.created_at:
            dt = asset_wrapper.asset.created_at
            if isinstance(dt, str):
                # Parse ISO format
                return dt[:10]  # Extract YYYY-MM-DD
            else:
                # datetime object
                return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    
    # Fallback: current date
    return datetime.now().strftime("%Y-%m-%d")


@typechecked
def _find_album_by_name(
    albums: AlbumCollectionWrapper,
    album_name: str
) -> Optional[str]:
    """Find album ID by name. Returns ID if found, None otherwise."""
    try:
        # Assuming AlbumCollectionWrapper has a method to search/get albums
        # Adjust based on actual API
        for album in albums.albums:
            if album.album_name == album_name:
                return album.id
    except Exception:
        pass
    return None
```

## Modification Points

### In `analyze_and_assign_album.py`

**Location**: After line ~55, in the `else` block handling "no valid album found"

**Current**:
```python
        else:
            log(
                f"[ALBUM ASSIGNMENT] No valid album found for asset '{asset_name}'. No assignment performed.",
                level=LogLevel.FOCUS,
            )
```

**Modified**:
```python
        else:
            from immich_autotag.assets.albums.create_album_if_missing_classification import \
                create_album_if_missing_classification
            
            created_album = create_album_if_missing_classification(asset_wrapper, tag_mod_report)
            if not created_album:
                log(
                    f"[ALBUM ASSIGNMENT] No valid album found for asset '{asset_name}'. No assignment performed.",
                    level=LogLevel.FOCUS,
                )
```

## Config Integration

**Already in `models.py`**:
```python
create_album_from_date_if_missing: bool = False
```

**In `user_config.py` (for user enabling)**:
```python
create_album_from_date_if_missing = True  # Set to True to enable auto album creation
```

## Reused Functions

| Function | Module | Purpose |
|----------|--------|---------|
| `_process_album_detection()` | `_process_album_detection.py` | Assign asset to album |
| `AlbumCollectionWrapper.create_album()` | `album_collection_wrapper.py` | Create album in Immich |
| `AssetResponseWrapper.get_tag_names()` | `asset_response_wrapper.py` | Get asset tags |
| `ConfigManager.get_instance()` | `config/manager.py` | Get config |

## Error Handling

1. **Config not enabled**: Return None silently (expected behavior)
2. **No date extractable**: Log WARN, skip album creation
3. **Album creation fails**: Log ERROR, return None (non-blocking)
4. **Asset assignment fails**: Log ERROR, return None (non-blocking)
5. **Exclusion tags present**: Log DEBUG, skip (expected behavior)

## Testing Strategy

- **Unit**: Album name generation, date extraction, exclusion logic
- **Integration**: Full flow with mock Immich API
- **Manual**: Enable flag in config, process assets, verify albums created

## Rollback Plan

Disable flag in config: `create_album_from_date_if_missing = False` (default)
