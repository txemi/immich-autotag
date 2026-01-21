"""
Album Permission Executor - Phase 2

Synchronizes album member permissions with configured rules.
Implements complete synchronization: config is source of truth (add + remove).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List
from uuid import UUID

from immich_client.api.albums import add_users_to_album as immich_add_users_to_album
from immich_client.api.albums import get_album_info as immich_get_album_info
from immich_client.api.albums import (
    remove_user_from_album as immich_remove_user_from_album,
)
from immich_client.api.users import search_users as immich_search_users
from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_client.models.album_user_role import AlbumUserRole
from typeguard import typechecked

from immich_autotag.albums.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.tags.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

import attrs


@attrs.define(auto_attribs=True, on_setattr=attrs.setters.validate)
class ResolveEmailsResult:
    resolved: Dict[str, str] = attrs.field(validator=attrs.validators.instance_of(dict))
    unresolved: List[str] = attrs.field(validator=attrs.validators.instance_of(list))

    def __iter__(self):
        # allow unpacking: resolved, unresolved = func(...)
        yield self.resolved
        yield self.unresolved


@typechecked
def _resolve_emails_to_user_ids(
    emails: List[str], context: ImmichContext
) -> ResolveEmailsResult:
    """
    Resolve email addresses to Immich user IDs.

    Returns:
        (email_to_id_map, unresolved_emails)
        - email_to_id_map: {email → user_id (UUID)}
        - unresolved_emails: List of emails that couldn't be found

    Fetches all users from Immich and maps their emails to IDs.
    """
    if not emails:
        return ResolveEmailsResult(resolved={}, unresolved=[])

    log_debug(f"[ALBUM_PERMISSIONS] Resolving {len(emails)} emails to user IDs")

    client = context.client
    try:
        all_users = immich_search_users.sync(client=client)
    except Exception as e:
        log(
            f"[ALBUM_PERMISSIONS] ERROR fetching user list: {e}",
            level=LogLevel.ERROR,
        )
        raise

    # Build email → user_id map
    email_to_id = {}
    for user in all_users:
        if user.email:
            email_to_id[user.email] = str(user.id)

    # Check which emails were resolved
    email_set = set(emails)
    resolved = {
        email: email_to_id[email] for email in email_set if email in email_to_id
    }
    unresolved = [email for email in email_set if email not in email_to_id]

    if unresolved:
        log(
            f"[ALBUM_PERMISSIONS] Warning: Could not resolve {len(unresolved)} emails to user IDs: {unresolved}",
            level=LogLevel.IMPORTANT,
        )

    log_debug(
        f"[ALBUM_PERMISSIONS] Resolved {len(resolved)}/{len(email_set)} emails to user IDs"
    )
    return ResolveEmailsResult(resolved=resolved, unresolved=unresolved)


@typechecked
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
        resolved_policy: Resolved policy with target members (emails)
        context: ImmichContext with API client
    """
    album_id = album_wrapper.get_album_id()
    album_name = album_wrapper.get_album_name()
    # Use the no-cache UUID accessor when interacting with APIs that expect a UUID
    album_uuid = album_wrapper.get_album_uuid_no_cache()

    report = ModificationReport.get_instance()

    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return

    # Resolve configured member emails to user IDs
    email_to_id_map, _ = _resolve_emails_to_user_ids(resolved_policy.members, context)
    target_user_ids = set(email_to_id_map.values())

    # Get current members from API (pass UUID directly)
    current_members = _get_current_members(album_uuid, context)
    current_user_ids = {str(member.user.id) for member in current_members}

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
        _remove_members_from_album(album_id, album_name, list(users_to_remove), context)
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


@typechecked
def _get_current_members(
    album_id: UUID, context: ImmichContext
) -> List[AlbumUserResponseDto]:
    """
    Fetch current album members from API.

    Returns list of album_user_response_dto objects with user_id attribute.
    """
    log_debug(f"[ALBUM_PERMISSIONS] Fetching current members for album {album_id}")

    client = context.client
    # `album_id` may be a `str` or a `UUID`. Pass it directly to the client
    # (the client accepts UUID objects); avoid double-wrapping with `UUID()`.
    response = immich_get_album_info.sync(
        id=album_id,
        client=client,
    )

    if response is None:
        log_debug(f"[ALBUM_PERMISSIONS] Album {album_id} not found")
        return []

    current_members = response.album_users or []
    log_debug(
        f"[ALBUM_PERMISSIONS] Album {album_id} has {len(current_members)} members"
    )
    if current_members:
        log_debug(
            f"[ALBUM_PERMISSIONS] First member attributes: {dir(current_members[0])}"
        )
        try:
            _ = current_members[0].__dict__
            has_dict = True
        except AttributeError:
            has_dict = False
        if has_dict:
            log_debug(
                f"[ALBUM_PERMISSIONS] First member __dict__: {current_members[0].__dict__}"
            )
    return current_members


@typechecked
def _add_members_to_album(
    album_id: str,
    album_name: str,
    user_ids: List[str],
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

    # Convert access_level string to AlbumUserRole
    role = AlbumUserRole.EDITOR if access_level == "editor" else AlbumUserRole.VIEWER

    # Build AddUsersDto
    album_users_dto = [
        AlbumUserAddDto(
            user_id=UUID(user_id),
            role=role,
        )
        for user_id in user_ids
    ]
    add_users_dto = AddUsersDto(album_users=album_users_dto)

    # Call API
    client = context.client
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


@typechecked
def _remove_members_from_album(
    album_id: str,
    album_name: str,
    user_ids: List[str],
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

    client = context.client
    for user_id in user_ids:
        response = immich_remove_user_from_album.sync_detailed(
            id=UUID(album_id),
            user_id=user_id,
            client=client,
        )
        log_debug(f"[ALBUM_PERMISSIONS] Removed user {user_id} from {album_name}")
