"""
Album Permission Executor - Phase 2

Synchronizes album member permissions with configured rules.
Implements complete synchronization: config is source of truth (add + remove).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from immich_client.api.albums import add_users_to_album as immich_add_users_to_album
from immich_client.api.albums import get_album_info as immich_get_album_info
from immich_client.api.albums import (
    remove_user_from_album as immich_remove_user_from_album,
)
from immich_client.client import AuthenticatedClient
from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_role import AlbumUserRole

from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.tags.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper


def sync_album_permissions(
    album_wrapper: "AlbumResponseWrapper",
    resolved_policy: ResolvedAlbumPolicy,
    context: ImmichContext,
) -> None:
    """
    Phase 2: Synchronize album permissions with configured rules.

    Complete sync strategy: config is source of truth.
    - PONER (add): Members in config but not in album
    - QUITAR (remove): Members in album but not in config

    Args:
        album_wrapper: Album wrapper with album data
        resolved_policy: Resolved policy with target members
        context: ImmichContext with API client
    """
    album = album_wrapper.album
    album_id = album.id
    album_name = album.album_name

    report = ModificationReport.get_instance()

    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return

    try:
        # Get current members from API
        current_members = _get_current_members(album_id, context)
        current_user_ids = {str(member.user_id) for member in current_members}

        # Extract target user IDs from resolved policy
        target_user_ids = set(resolved_policy.members)

        # Calculate diff
        users_to_add = target_user_ids - current_user_ids
        users_to_remove = current_user_ids - target_user_ids

        # Phase 2A: PONER (add members)
        if users_to_add:
            _add_members_to_album(
                album_id,
                album_name,
                list(users_to_add),
                resolved_policy.access_level,
                context,
            )
            report.add_album_permission_modification(
                kind=ModificationKind.ALBUM_PERMISSION_SHARED,
                album=album_wrapper,
                matched_rules=resolved_policy.matched_rules,
                groups=resolved_policy.groups,
                members=list(users_to_add),
                access_level=resolved_policy.access_level,
            )

        # Phase 2B: QUITAR (remove members)
        if users_to_remove:
            _remove_members_from_album(
                album_id, album_name, list(users_to_remove), context
            )
            report.add_album_permission_modification(
                kind=ModificationKind.ALBUM_PERMISSION_REMOVED,
                album=album_wrapper,
                matched_rules=resolved_policy.matched_rules,
                groups=resolved_policy.groups,
                members=list(users_to_remove),
                access_level="none",
            )

        if users_to_add or users_to_remove:
            log(
                f"[ALBUM_PERMISSIONS] Synced {album_name}: "
                f"+{len(users_to_add)} PONER, -{len(users_to_remove)} QUITAR",
                level=LogLevel.FOCUS,
            )
        else:
            log_debug(f"[ALBUM_PERMISSIONS] {album_name}: No changes needed")

    except Exception as e:
        log(
            f"[ALBUM_PERMISSIONS] ERROR syncing {album_name}: {e}",
            level=LogLevel.ERROR,
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_SHARE_FAILED,
            album=album_wrapper,
            matched_rules=resolved_policy.matched_rules,
            groups=resolved_policy.groups,
            members=[],
            access_level="error",
            extra={"error": str(e)},
        )


def _get_current_members(album_id: str, context: ImmichContext) -> list[Any]:
    """
    Fetch current album members from API.

    Returns list of album_user_response_dto objects with user_id attribute.
    """
    log_debug(f"[ALBUM_PERMISSIONS] Fetching current members for album {album_id}")

    try:
        # Cast client to AuthenticatedClient for API call
        client = context.client
        if not isinstance(client, AuthenticatedClient):
            raise RuntimeError("Client must be AuthenticatedClient")

        response = immich_get_album_info.sync(
            id=UUID(album_id),
            client=client,
        )

        if response is None:
            log_debug(f"[ALBUM_PERMISSIONS] Album {album_id} not found")
            return []

        current_members = response.album_users or []
        log_debug(
            f"[ALBUM_PERMISSIONS] Album {album_id} has {len(current_members)} members"
        )
        return current_members

    except Exception as e:
        log(
            f"[ALBUM_PERMISSIONS] ERROR fetching album members for {album_id}: {e}",
            level=LogLevel.ERROR,
        )
        raise


def _add_members_to_album(
    album_id: str,
    album_name: str,
    user_ids: list[str],
    access_level: str,
    context: ImmichContext,
) -> None:
    """
    Add members to album (PONER).

    Args:
        album_id: UUID of the album
        album_name: Name of the album
        user_ids: List of user IDs to add
        access_level: "editor" or "viewer" for access level
        context: ImmichContext with API client
    """
    if not user_ids:
        return

    log(
        f"[ALBUM_PERMISSIONS] Adding {len(user_ids)} members to {album_name} "
        f"(access: {access_level})",
        level=LogLevel.PROGRESS,
    )

    try:
        # Convert access_level string to AlbumUserRole
        role = (
            AlbumUserRole.EDITOR if access_level == "editor" else AlbumUserRole.VIEWER
        )

        # Build AddUsersDto
        album_users_dto = [
            AlbumUserAddDto(
                user_id=UUID(user_id),
                role=role,
            )
            for user_id in user_ids
        ]
        add_users_dto = AddUsersDto(album_users=album_users_dto)

        # Cast client to AuthenticatedClient for API call
        client = context.client
        if not isinstance(client, AuthenticatedClient):
            raise RuntimeError("Client must be AuthenticatedClient")

        # Call API
        response = immich_add_users_to_album.sync(
            id=UUID(album_id),
            body=add_users_dto,
            client=client,
        )

        if response is not None:
            log_debug(
                f"[ALBUM_PERMISSIONS] Successfully added {len(user_ids)} "
                f"members to {album_name}"
            )
        else:
            log(
                f"[ALBUM_PERMISSIONS] WARNING: add_users_to_album returned "
                f"None for {album_name}",
                level=LogLevel.IMPORTANT,
            )

    except Exception as e:
        log(
            f"[ALBUM_PERMISSIONS] ERROR adding members to {album_name}: {e}",
            level=LogLevel.ERROR,
        )
        raise


def _remove_members_from_album(
    album_id: str,
    album_name: str,
    user_ids: list[str],
    context: ImmichContext,
) -> None:
    """
    Remove members from album (QUITAR).

    Args:
        album_id: UUID of the album
        album_name: Name of the album
        user_ids: List of user IDs to remove
        context: ImmichContext with API client
    """
    if not user_ids:
        return

    log(
        f"[ALBUM_PERMISSIONS] Removing {len(user_ids)} members from {album_name}",
        level=LogLevel.PROGRESS,
    )

    # Cast client to AuthenticatedClient for API call
    client = context.client
    if not isinstance(client, AuthenticatedClient):
        raise RuntimeError("Client must be AuthenticatedClient")

    failed_removals = []

    for user_id in user_ids:
        try:
            response = immich_remove_user_from_album.sync_detailed(
                id=UUID(album_id),
                user_id=user_id,
                client=client,
            )
            log_debug(f"[ALBUM_PERMISSIONS] Removed user {user_id} from {album_name}")

        except Exception as e:
            log(
                f"[ALBUM_PERMISSIONS] ERROR removing user {user_id} from "
                f"{album_name}: {e}",
                level=LogLevel.IMPORTANT,
            )
            failed_removals.append((user_id, str(e)))

    if failed_removals:
        log(
            f"[ALBUM_PERMISSIONS] {len(failed_removals)} removals failed for "
            f"{album_name}",
            level=LogLevel.IMPORTANT,
        )
