"""Duplicate albums management package.

Provides a manager to collect duplicate-album occurrences and optionally
perform an auto-merge (move assets then delete duplicate album) when
configured.
"""

from .manager import DuplicateAlbumManager

__all__ = ["DuplicateAlbumManager"]
