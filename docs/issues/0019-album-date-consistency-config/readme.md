---
status: Proposed
version: v1.0
created: 2026-01-15
updated: 2026-01-15
---

# 0019 - Album Date Consistency Configuration Refactor

**Tech Stack:** #Python #Configuration #Pydantic #Albums #DateConsistency

## Context
The `autotag_album_date_mismatch` configuration and its related logic are currently located in `DuplicateProcessingConfig`, but album date consistency checking is **not related to duplicate detection**. This is a semantic misplacement that causes confusion.

Additionally, the date threshold is hardcoded to 6 months in the implementation, making it impossible to fine-tune the sensitivity without code changes.

## Problem Statement
1. **Semantic Problem**: Album date consistency is an independent check that happens after classification, not part of duplicate processing
2. **Configuration Problem**: `autotag_album_date_mismatch` is in the wrong config section (`duplicate_processing` instead of its own section)
3. **Flexibility Problem**: The 6-month threshold is hardcoded, preventing iterative refinement of false positives
4. **Granularity Problem**: Using months as a unit is too coarse for fine-grained adjustments (users need daily precision)

## Current Implementation
- Config: `duplicate_processing.autotag_album_date_mismatch`
- Logic: `immich_autotag/assets/consistency_checks/_album_date_consistency.py`
- Hardcoded: `months_threshold=6` parameter in `check_album_date_consistency()`
- Called: As independent step in `process_single_asset.py` after classification

## Proposed Solution
Create a new `AlbumDateConsistencyConfig` class and move the configuration there:

```python
@define
class AlbumDateConsistencyConfig:
    """Configuration for album date consistency checks."""
    
    enabled: bool = True
    """Whether to check album date consistency."""
    
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    """Tag to mark assets with album date mismatches."""
    
    threshold_days: int = 180  # 6 months as initial default
    """Maximum allowed difference in days between album and asset dates."""
```

### Rationale for Days Instead of Months
- **Fine granularity**: Allows incremental adjustments (180 → 90 → 60 → 30 → 7 days)
- **Intuitive**: "30 days difference" is clearer than "1 month" (which month? 28/30/31 days?)
- **Flexible**: Enables strict tolerances (e.g., 1-2 days) if needed in the future
- **Iterative workflow**: Users can gradually reduce threshold as they fix errors

### Migration Path
1. Add new `AlbumDateConsistencyConfig` to `UserConfig`
2. Update `user_config_template.py` and `user_config_template.yaml` with new section
3. Modify `_album_date_consistency.py` to accept `threshold_days` parameter from config
4. Remove `autotag_album_date_mismatch` from `DuplicateProcessingConfig` (breaking change)
5. Update config documentation and migration guide

## Definition of Done (DoD)
- [ ] Create `AlbumDateConsistencyConfig` class in `immich_autotag/config/models.py`
- [ ] Add `album_date_consistency: AlbumDateConsistencyConfig` field to `UserConfig`
- [ ] Update `user_config_template.py` with new config section
- [ ] Update `user_config_template.yaml` with new config section
- [ ] Remove `autotag_album_date_mismatch` from `DuplicateProcessingConfig`
- [ ] Update `check_album_date_consistency()` signature to accept `threshold_days` parameter
- [ ] Update call site in `process_single_asset.py` to pass config value
- [ ] Convert hardcoded 6 months to 180 days as default
- [ ] Update config validation if needed
- [ ] Test with various threshold values (180, 90, 30, 7 days)
- [ ] Update documentation explaining the new config section
- [ ] Add migration note to CHANGELOG for breaking config change

## Impact Analysis
- **Breaking Change**: Users must update their config files to move `autotag_album_date_mismatch` from `duplicate_processing` to `album_date_consistency`
- **Version**: Requires major/minor version bump (v1.0+ recommended)
- **Backward Compatibility**: Could add temporary config migration logic if needed
- **Performance**: No performance impact, only configuration structure change

## Related Issues
- Issue 0009: Configuration System Refactor (in progress)
