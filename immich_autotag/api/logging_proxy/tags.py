"""
Logging proxy for tag operations (re-exports from specialized modules).

This module provides backward compatibility by re-exporting functions from:
- add_tags: Functions for adding tags to assets
- create_tag: Functions for creating tags
- remove_tags: Functions for removing tags from assets and managing tag lifecycle

New code should import directly from these modules instead.
"""

from __future__ import annotations

# Re-export add tag functions
from immich_autotag.api.logging_proxy.add_tags import (
    logging_tag_assets,
    logging_tag_assets_safe,
)

# Re-export create tag functions
from immich_autotag.api.logging_proxy.create_tag import logging_create_tag

# Re-export remove tag functions
from immich_autotag.api.logging_proxy.remove_tags import (
    logging_delete_tag,
    logging_untag_assets,
    logging_untag_assets_safe,
)

__all__ = [
    "logging_tag_assets",
    "logging_tag_assets_safe",
    "logging_untag_assets",
    "logging_untag_assets_safe",
    "logging_delete_tag",
    "logging_create_tag",
]
