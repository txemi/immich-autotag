"""
Legacy import module for backward compatibility.
The validate_and_update_asset_classification function has been moved.
This file provides imports from the new location.
"""

from __future__ import annotations

# Import from new location for backward compatibility
from immich_autotag.assets.validation.validate_and_update_asset_classification import (
    validate_and_update_asset_classification,
)

# Re-export for backward compatibility
__all__ = ["validate_and_update_asset_classification"]
