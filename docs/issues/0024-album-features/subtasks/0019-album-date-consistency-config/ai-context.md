# AI Context for Issue 0019

## Problem Analysis
This issue addresses a semantic and architectural problem in the configuration system:

1. **Misplaced Configuration**: The `autotag_album_date_mismatch` tag configuration is currently in `DuplicateProcessingConfig`, but album date consistency checking has nothing to do with duplicate detection
2. **Hardcoded Logic**: The date difference threshold (6 months) is hardcoded in the implementation, making it impossible to adjust without code changes
3. **Unit Granularity**: Using months is too coarse for iterative refinement workflows

## Current Architecture

### Configuration Location (Wrong)
```python
# In immich_autotag/config/models.py
@define
class DuplicateProcessingConfig:
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    # ... other duplicate-related fields
```

### Implementation Location (Correct)
```python
# In immich_autotag/assets/consistency_checks/_album_date_consistency.py
def check_album_date_consistency(
    asset: AssetResponseWrapper,
    months_threshold: int = 6,  # HARDCODED
) -> bool:
    # Checks if asset date differs from album date by more than threshold
    # Returns True if mismatch detected
```

### Call Site (Independent Step)
```python
# In immich_autotag/assets/process_single_asset.py
async def process_single_asset(...):
    # ... classification logic ...
    
    # Independent consistency check (NOT part of duplicates)
    await check_album_date_consistency(
        asset_wrapper=asset_wrapper,
        # threshold passed as default parameter
    )
```

## Proposed Architecture

### New Configuration Class
```python
# In immich_autotag/config/models.py
@define
class AlbumDateConsistencyConfig:
    """Configuration for album date consistency checks."""
    
    enabled: bool = True
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    threshold_days: int = 180  # 6 months = ~180 days
```

### Updated UserConfig
```python
@define
class UserConfig:
    classification: ClassificationConfig
    duplicate_processing: DuplicateProcessingConfig  # Remove autotag_album_date_mismatch
    album_date_consistency: AlbumDateConsistencyConfig  # NEW SECTION
    # ... other fields
```

### Updated Function Signature
```python
def check_album_date_consistency(
    asset: AssetResponseWrapper,
    threshold_days: int,  # From config, not hardcoded
) -> bool:
    # Convert days to timedelta for comparison
    threshold = timedelta(days=threshold_days)
    # ... rest of logic
```

### Updated Call Site
```python
async def process_single_asset(...):
    # ... classification logic ...
    
    # Get config from singleton
    config = ConfigManager().user_config
    
    if config.album_date_consistency.enabled:
        await check_album_date_consistency(
            asset_wrapper=asset_wrapper,
            threshold_days=config.album_date_consistency.threshold_days,
        )
```

## Files to Modify

### Configuration Files
1. `immich_autotag/config/models.py`:
   - Create `AlbumDateConsistencyConfig` class
   - Add field to `UserConfig`
   - Remove `autotag_album_date_mismatch` from `DuplicateProcessingConfig`

2. `immich_autotag/config/user_config_template.py`:
   - Add new `album_date_consistency` section
   - Remove from `duplicate_processing`

3. `immich_autotag/config/user_config_template.yaml`:
   - Add new `album_date_consistency` section
   - Remove from `duplicate_processing`

### Implementation Files
4. `immich_autotag/assets/consistency_checks/_album_date_consistency.py`:
   - Change parameter from `months_threshold: int = 6` to `threshold_days: int`
   - Update timedelta calculation to use days instead of months approximation

5. `immich_autotag/assets/process_single_asset.py`:
   - Update call to pass `config.album_date_consistency.threshold_days`
   - Add check for `config.album_date_consistency.enabled`

### Documentation Files
6. `CHANGELOG.md`: Add breaking change notice
7. Documentation about configuration structure

## Key Implementation Details

### Days vs Months Conversion
Current implementation likely does something like:
```python
threshold = timedelta(days=months_threshold * 30)  # Approximation
```

New implementation:
```python
threshold = timedelta(days=threshold_days)  # Exact
```

### Default Value Equivalence
- Old: 6 months → approximately 180 days
- New: 180 days (explicit)

### Typical Refinement Workflow
Users can iteratively reduce threshold:
1. Start: `threshold_days: 180` (catch major errors)
2. After cleanup: `threshold_days: 90` (3 months)
3. After cleanup: `threshold_days: 60` (2 months)
4. After cleanup: `threshold_days: 30` (1 month)
5. Final strictness: `threshold_days: 7` (1 week)

## Testing Strategy
1. Unit tests: Verify config parsing with new section
2. Integration tests: Verify consistency check uses config value
3. Manual tests: Test with various threshold values (180, 90, 30, 7 days)
4. Migration test: Verify old config warns about deprecated field

## Migration Notes for Users
Breaking change notice in CHANGELOG:
```markdown
### Breaking Changes
- **Configuration**: `duplicate_processing.autotag_album_date_mismatch` moved to new `album_date_consistency` section
- **Migration**: Move your config and add `threshold_days` parameter (default: 180)
- **Example**:
  ```yaml
  # OLD (deprecated)
  duplicate_processing:
    autotag_album_date_mismatch: "autotag_album_date_mismatch"
  
  # NEW (required)
  album_date_consistency:
    enabled: true
    autotag_album_date_mismatch: "autotag_album_date_mismatch"
    threshold_days: 180  # Adjust as needed
  ```
```
