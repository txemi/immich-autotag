"""
Album Permissions Module

Phase 1: Detection & logging (dry-run)
Phase 2: Complete synchronization of album permissions

Configuration is the source of truth: only members in config will have access.
"""

from immich_autotag.permissions.album_permission_executor import (
    sync_album_permissions,
)
from immich_autotag.permissions.process_album_permissions import (
    process_album_permissions,
)

__all__ = ["process_album_permissions", "sync_album_permissions"]
