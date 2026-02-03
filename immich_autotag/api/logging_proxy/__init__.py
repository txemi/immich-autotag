"""
Logging Proxy Layer

This layer wraps immich_proxy functions to add automatic event logging,
statistics tracking, and modification reporting.

Module Organization:
====================

   tags/tag_assets.py: Functions for adding tags to assets
    ├─ logging_tag_assets()
    └─ logging_tag_assets_safe() (with error handling)

    remove_tags.py: Functions for removing tags
    ├─ logging_untag_assets()
    └─ logging_delete_tag()

    tags.py: Re-exports (backward compatibility)
   └─ Imports from tags/tag_assets.py and remove_tags.py

Architecture:
=============

    Level 1: immich_proxy/*
    ├─ Pure API calls (no side effects)
    ├─ Direct wrappers around immich_client SDK
    └─ Examples: proxy_delete_tag(), proxy_create_tag(), proxy_tag_assets()

    Level 2: logging_proxy/* (THIS LAYER)
    ├─ Wraps immich_proxy functions
    ├─ Receives rich wrapper objects (TagWrapper, AssetWrapper, etc.)
    ├─ Handles logging, statistics, event recording
    └─ Examples: logging_delete_tag(), logging_create_tag(), logging_tag_assets()

Key Principles:
===============

1. WRAPPER OBJECTS: Accept TagWrapper/AssetWrapper instead of raw IDs
   - Type-safe operations
   - Full context available
   - Reduces parameter passing errors

2. SINGLE SOURCE OF TRUTH: ModificationReport is the definitive logging source
   - All logging delegated to ModificationReport
   - Centralized audit trail
   - Consistent statistics tracking

3. NO DUPLICATION: Avoid logging the same event twice
   - If ModificationReport.add_tag_modification() logs it, don't log again here
   - Check if ModificationKind exists before adding events

4. DELEGATED RESPONSIBILITIES:
   - API Call: immich_proxy layer
   - Logging: ModificationReport
   - Statistics: StatisticsManager (via ModificationReport)
   - Event Recording: ModificationReport

Usage Example:
==============

    # ❌ Old way (dispersed and error-prone):
    proxy_delete_tag(client=client, tag_id=TagUUID.from_string(tag.id))
    print(f"[CLEANUP] Deleted tag: {tag.name}")  # Manual logging
    report.add_modification(...)                  # Manual event tracking

    # ✅ New way (centralized and robust):
    from immich_autotag.api.logging_proxy.tags import logging_delete_tag
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

    tag_wrapper = TagWrapper(tag_dto)
    logging_delete_tag(client=client, tag=tag_wrapper, reason="cleanup")
    # → Automatically: API call + logging + event recording + statistics

Submodules:
===========

- tags.py: Tag operations (create, delete, tag_assets, untag_assets)
- albums.py: Album operations (to be implemented)
- assets.py: Asset operations (to be implemented)
"""
