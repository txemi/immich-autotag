# Technical Design: Album Date Consistency Configuration Refactor

## Overview
Refactor the album date consistency configuration from `DuplicateProcessingConfig` to a dedicated `AlbumDateConsistencyConfig` class, making the threshold configurable in days instead of hardcoded months.

## Architecture Changes

### 1. New Configuration Model

```python
# File: immich_autotag/config/models.py

from attrs import define

@define
class AlbumDateConsistencyConfig:
    """Configuration for album date consistency checks.
    
    This check compares the asset's taken date with its album's date
    and tags mismatches for user review.
    """
    
    enabled: bool = True
    """Whether to perform album date consistency checks."""
    
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    """Tag name to apply when asset date differs significantly from album date."""
    
    threshold_days: int = 180
    """Maximum allowed difference in days between album and asset dates.
    
    Default is 180 days (~6 months). Assets with larger differences are tagged.
    Recommended workflow: Start with 180, then gradually reduce (90, 60, 30, 7)
    as you clean up mismatches.
    """
```

### 2. UserConfig Integration

```python
# File: immich_autotag/config/models.py

@define
class UserConfig:
    """Complete user configuration."""
    
    classification: ClassificationConfig
    duplicate_processing: DuplicateProcessingConfig  # Remove autotag_album_date_mismatch
    album_date_consistency: AlbumDateConsistencyConfig  # NEW
    # ... other existing fields
```

### 3. DuplicateProcessingConfig Cleanup

```python
# File: immich_autotag/config/models.py

@define
class DuplicateProcessingConfig:
    """Configuration for duplicate asset detection and processing."""
    
    enabled: bool = True
    autotag_duplicate: str = "autotag_duplicate"
    autotag_original: str = "autotag_original"
    # REMOVED: autotag_album_date_mismatch (moved to AlbumDateConsistencyConfig)
    
    comparison_fields: list[str] = field(factory=lambda: [
        "originalFileName",
        "localDateTime",
        "exifInfo.dateTimeOriginal"
    ])
```

## Implementation Changes

### 4. Consistency Check Function

```python
# File: immich_autotag/assets/consistency_checks/_album_date_consistency.py

from datetime import timedelta

async def check_album_date_consistency(
    asset_wrapper: AssetResponseWrapper,
    threshold_days: int,  # Changed from months_threshold with default
    modification_report: ModificationReport,
    autotag_name: str,
) -> bool:
    """Check if asset date is consistent with its album date.
    
    Args:
        asset_wrapper: The asset to check
        threshold_days: Maximum allowed difference in days (from config)
        modification_report: Report to record changes
        autotag_name: Tag name to apply/remove (from config)
    
    Returns:
        True if mismatch detected, False otherwise
    """
    if not asset_wrapper.albums:
        return False
    
    asset_date = asset_wrapper.local_date_time
    if not asset_date:
        return False
    
    # Use days directly instead of months approximation
    threshold = timedelta(days=threshold_days)
    
    for album in asset_wrapper.albums:
        album_date = parse_album_date(album.album_name)
        if not album_date:
            continue
        
        date_diff = abs((asset_date - album_date).days)
        
        if date_diff > threshold_days:
            # Tag the mismatch
            if autotag_name not in asset_wrapper.tags:
                await asset_wrapper.add_tag(autotag_name)
                modification_report.add_modification(
                    asset_id=asset_wrapper.id,
                    kind=ModificationKind.TAG_ADDED,
                    detail=f"Album date mismatch: {date_diff} days difference (threshold: {threshold_days})"
                )
            return True
    
    # No mismatch found, remove tag if present
    if autotag_name in asset_wrapper.tags:
        await asset_wrapper.remove_tag(autotag_name)
        modification_report.add_modification(
            asset_id=asset_wrapper.id,
            kind=ModificationKind.TAG_REMOVED,
            detail=f"Album date now consistent (within {threshold_days} days)"
        )
    
    return False
```

### 5. Call Site Update

```python
# File: immich_autotag/assets/process_single_asset.py

async def process_single_asset(
    asset_wrapper: AssetResponseWrapper,
    # ... other parameters
) -> None:
    """Process a single asset through classification and consistency checks."""
    
    config = ConfigManager().user_config
    
    # ... classification logic ...
    
    # Album date consistency check (independent step)
    if config.album_date_consistency.enabled:
        await check_album_date_consistency(
            asset_wrapper=asset_wrapper,
            threshold_days=config.album_date_consistency.threshold_days,
            modification_report=modification_report,
            autotag_name=config.album_date_consistency.autotag_album_date_mismatch,
        )
```

## Configuration Templates

### 6. Python Template

```python
# File: immich_autotag/config/user_config_template.py

# Album Date Consistency Configuration
album_date_consistency = AlbumDateConsistencyConfig(
    enabled=True,
    autotag_album_date_mismatch="autotag_album_date_mismatch",
    threshold_days=180,  # 6 months - adjust based on your needs
)

# Remove from duplicate_processing:
duplicate_processing = DuplicateProcessingConfig(
    enabled=True,
    autotag_duplicate="autotag_duplicate",
    autotag_original="autotag_original",
    # autotag_album_date_mismatch removed - now in album_date_consistency
)
```

### 7. YAML Template

```yaml
# File: immich_autotag/config/user_config_template.yaml

# Album Date Consistency
# Checks if asset dates match their album dates
album_date_consistency:
  enabled: true
  autotag_album_date_mismatch: "autotag_album_date_mismatch"
  threshold_days: 180  # Maximum allowed difference in days
  # Recommended workflow:
  # - Start: 180 days (6 months) - catch major errors
  # - After cleanup: 90 days (3 months)
  # - After cleanup: 60 days (2 months)  
  # - After cleanup: 30 days (1 month)
  # - Final: 7 days (1 week) for strict consistency

# Duplicate Processing
duplicate_processing:
  enabled: true
  autotag_duplicate: "autotag_duplicate"
  autotag_original: "autotag_original"
  # Note: autotag_album_date_mismatch moved to album_date_consistency section
```

## Migration Strategy

### Phase 1: Add New Config (Non-Breaking)
1. Add `AlbumDateConsistencyConfig` class
2. Add field to `UserConfig` with default value
3. Update templates with new section
4. Keep old field in `DuplicateProcessingConfig` for now (deprecated)

### Phase 2: Update Implementation
1. Update `check_album_date_consistency()` to accept config parameters
2. Update call site to use new config section
3. Add deprecation warning if old config field is set

### Phase 3: Breaking Change (v1.0)
1. Remove `autotag_album_date_mismatch` from `DuplicateProcessingConfig`
2. Update CHANGELOG with migration guide
3. Bump version to v1.0

## Testing Plan

### Unit Tests
```python
def test_album_date_consistency_config_defaults():
    config = AlbumDateConsistencyConfig()
    assert config.enabled is True
    assert config.threshold_days == 180
    assert config.autotag_album_date_mismatch == "autotag_album_date_mismatch"

def test_album_date_consistency_custom_threshold():
    config = AlbumDateConsistencyConfig(threshold_days=30)
    assert config.threshold_days == 30

def test_check_consistency_uses_config_threshold():
    # Test that function respects configured threshold
    pass

def test_threshold_edge_cases():
    # Test with 1 day, 7 days, 180 days, 365 days
    pass
```

### Integration Tests
```python
async def test_process_asset_with_date_consistency():
    # Test full pipeline uses new config
    config = ConfigManager()
    config.user_config.album_date_consistency.threshold_days = 30
    
    # Process asset with 60-day mismatch
    # Verify tag is added
    
    # Process asset with 20-day mismatch  
    # Verify no tag is added
```

## Rollout Plan

1. **Create branch**: `feature/album-date-consistency-config`
2. **Implement changes**: Follow order above (config → implementation → templates)
3. **Test thoroughly**: Unit + integration tests
4. **Update documentation**: CHANGELOG, config docs
5. **Merge to main**: After review
6. **Release**: Include in v1.0 with migration guide

## Documentation Updates

### CHANGELOG.md
```markdown
## [v1.0.0] - 2026-01-15

### Breaking Changes
- **Configuration**: `duplicate_processing.autotag_album_date_mismatch` moved to new `album_date_consistency` section
- **New Feature**: Album date threshold now configurable in days (was hardcoded to 6 months)

### Migration Guide
Update your configuration file:

**Before:**
```yaml
duplicate_processing:
  autotag_album_date_mismatch: "autotag_album_date_mismatch"
```

**After:**
```yaml
album_date_consistency:
  enabled: true
  autotag_album_date_mismatch: "autotag_album_date_mismatch"
  threshold_days: 180  # Adjust as needed
```

### Added
- New `AlbumDateConsistencyConfig` for semantic clarity
- Configurable `threshold_days` parameter for fine-grained control
- Support for iterative threshold refinement workflow
```

## Future Enhancements
- Add statistics: "X assets have date mismatches > Y days"
- Add report: List of assets with largest date differences
- Consider multiple threshold levels (warning vs error)
- Support per-album date tolerance overrides
