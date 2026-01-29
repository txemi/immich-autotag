
from __future__ import annotations
from typing import Sequence
# Helper to remove members from album

"""
Album Permission Executor - Phase 2

Synchronizes album member permissions with configured rules.
Implements complete synchronization: config is source of truth (add + remove).
"""

from typing import TYPE_CHECKING, Dict, List
from uuid import UUID

from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_client.models.album_user_role import AlbumUserRole
from typeguard import typechecked

from immich_autotag.albums.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.api.immich_proxy.albums import proxy_add_users_to_album
from immich_autotag.api.immich_proxy.permissions import (
    proxy_remove_user_from_album,
    proxy_search_users,
)
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
# This file has been modularized into the album_permission_executor/ package.
# Each function/class now lives in its own file in the package.
# Update your imports to use the new structure, e.g.:
# from .album_permission_executor.resolve_emails_to_user_ids import _resolve_emails_to_user_ids