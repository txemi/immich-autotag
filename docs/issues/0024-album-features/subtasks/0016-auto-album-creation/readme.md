---
status: Not Started
version: v1.0
created: 2026-01-14
updated: 2026-01-14
---

# 0016 - Auto Album Creation from Date When No Classification Album Found

**Tech Stack:** #Python #Configuration #Albums #Classification

## Context
Currently, assets that cannot be assigned to any classification album (according to configured patterns) remain unorganized. This feature provides a fallback mechanism to automatically create temporary albums based on the asset's date, giving users an organized "inbox" for unclassified assets.

The feature is controlled by the config flag `create_album_from_date_if_missing` (disabled by default for safety).

## Problem Statement
When an asset does not match any classification album pattern:
- It remains in the main "Recents" view without clear organization
- Users have no automatic fallback for organizing "unknown" assets
- Manual album creation for these assets is tedious and error-prone

## Proposed Solution
- Automatically create albums with pattern: `YYYY-MM-DD-autotag-temp-unclassified`
- Reuse existing albums if they already exist (same date)
- Assign unclassified assets to these temporary albums
- Users can then review, rename, or delete these albums as needed

## Definition of Done (DoD)
- [ ] New function `create_album_if_missing_classification()` implemented
- [ ] Integration in `analyze_and_assign_album()` completed
- [ ] Config flag tested (enabled/disabled behavior)
- [ ] Album name generation follows pattern `YYYY-MM-DD-autotag-temp-*`
- [ ] Album reuse logic verified
- [ ] All modifications tracked in `ModificationReport`
- [ ] Logging at FOCUS level for significant events
- [ ] Unit tests for album generation and date extraction
- [ ] Backward compatible (disabled by default)
- [ ] Code style consistent with project (typechecked, imports, structure)

## Entry Point
- **File**: `immich_autotag/assets/albums/analyze_and_assign_album.py`
- **Function**: `analyze_and_assign_album()`

## New Implementation
- **File**: `immich_autotag/assets/albums/create_album_if_missing_classification.py`
- **Function**: `create_album_if_missing_classification(asset_wrapper, tag_mod_report)`

## Related Issues
- #0009: Config system refactor (established the `create_album_from_date_if_missing` flag)
- #0004: Album detection (existing album-related logic to reuse)

## References
- See `design/` folder for technical details
- See `ai-context.md` for development context
