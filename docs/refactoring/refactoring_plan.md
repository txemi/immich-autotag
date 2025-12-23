# Refactoring Plan: Immich Autotag

This document details the proposed refactoring of the codebase, specifying where each function and class will be moved as the project is modularized.

## Package Structure Proposal

```
autotag/
    __init__.py
    core/
        __init__.py
        asset_wrapper.py
        album_wrapper.py
        tag_wrapper.py
        context.py
    albums/
        __init__.py
        album_detection.py
        album_api.py
    tags/
        __init__.py
        tag_api.py
        tag_logic.py
    api/
        __init__.py
        immich_client.py
        models.py
    logging/
        __init__.py
        modification_report.py
    utils/
        __init__.py
        helpers.py
```

## Class and Function Mapping

### core/
- `AssetResponseWrapper` → asset_wrapper.py
- `AlbumResponseWrapper` → album_wrapper.py
- `TagCollectionWrapper` → tag_wrapper.py
- `ImmichContext` → context.py
- `MatchClassificationResult` → asset_wrapper.py

### albums/
- `AlbumFolderAnalyzer` → album_detection.py
- Album API integration functions → album_api.py

### tags/
- Tag API integration functions → tag_api.py
- Tag conversion logic, classification logic → tag_logic.py

### api/
- Immich API client setup and wrappers → immich_client.py
- Data models (DTOs, etc.) → models.py

### logging/
- `TagModificationReport` (to be generalized for albums/tags) → modification_report.py

### utils/
- Helper functions, shared utilities → helpers.py

## Next Steps
- Start by extracting the core wrappers and analyzers into their respective modules.
- Gradually move API logic and helpers into dedicated files.
- Generalize logging to support both tags and albums.
- Update imports in main.py and other entry points to use the new structure.

---

This plan will be updated as the refactoring progresses. Each module should include clear docstrings and type annotations.