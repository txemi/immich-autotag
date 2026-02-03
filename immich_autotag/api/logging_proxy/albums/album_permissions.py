"""
Logging proxy for album permission operations.

This module re-exports permission functions from specialized submodules:
- albums/add_users_to_album: Functions for adding members to albums
- remove_members: Functions for removing members from albums

Design: The ModificationReport is the single source of truth for all logging
and event tracking. This layer delegates all logging responsibilities to it.
"""

from immich_autotag.api.logging_proxy.albums.add_users_to_album import (
    logging_add_members_to_album,
    logging_add_user_to_album,
)
from immich_autotag.api.logging_proxy.remove_members import (
    logging_remove_members_from_album,
)

__all__ = [
    # Add members functions
    "logging_add_members_to_album",
    "logging_add_user_to_album",
    # Remove members functions
    "logging_remove_members_from_album",
]
