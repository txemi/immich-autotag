"""
Legacy import module for backward compatibility.
All classes and functions have been moved to their respective modules.
This file provides imports from the new locations.
"""

from __future__ import annotations

# Import from new locations for backward compatibility
from immich_autotag.assets.albums._process_album_detection import (
    _process_album_detection,
)
from immich_autotag.assets.albums.album_decision import AlbumDecision
from immich_autotag.assets.albums.analyze_and_assign_album import (
    analyze_and_assign_album,
)
from immich_autotag.assets.albums.decide_album_for_asset import decide_album_for_asset
from immich_autotag.assets.duplicates._duplicate_albums_info import DuplicateAlbumsInfo
from immich_autotag.assets.duplicates._get_album_from_duplicates import (
    get_album_from_duplicates,
)
from immich_autotag.assets.process.process_single_asset import process_single_asset

# Re-export all symbols for backward compatibility
__all__ = [
    "DuplicateAlbumsInfo",
    "get_album_from_duplicates",
    "AlbumDecision",
    "decide_album_for_asset",
    "analyze_and_assign_album",
    "_process_album_detection",
    "process_single_asset",
]
