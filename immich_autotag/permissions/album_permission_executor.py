"""
Album Permission Executor - Phase 2

Synchronizes album member permissions with configured rules.
Implements complete synchronization: config is source of truth (add + remove).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List
from uuid import UUID

from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_client.models.album_user_role import AlbumUserRole
from typeguard import typechecked

from immich_autotag.albums.permissions.album_policy_resolver import ResolvedAlbumPolicy
from immich_autotag.api.immich_proxy.albums import proxy_add_users_to_album
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport

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

    all_users = immich_search_users.sync(client=client)
    if all_users is None:
        all_users = []

    # Build email → user_id map
    email_to_id = {}
    for user in all_users:
        if user.email:
            email_to_id[user.email] = str(user.id)

    # Check which emails were resolved
    email_set = set(emails)
    resolved: Dict[str, str] = {
        email: email_to_id[email] for email in email_set if email in email_to_id
    }
    unresolved: List[str] = [email for email in email_set if email not in email_to_id]

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
def _get_current_members(
    album_id: UUID, context: ImmichContext
) -> List[AlbumUserResponseDto]:
    """
    Fetch current album members from API.

    Returns list of album_user_response_dto objects with user_id attribute.
    """
    log_debug(f"[ALBUM_PERMISSIONS] Fetching current members for album {album_id}")

    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )

    # Try to get the album wrapper from the collection first
    collection = AlbumCollectionWrapper.get_instance()
    wrapper = collection.find_album_by_id(album_id)
    album_members = wrapper.get_album_members()
    if album_members:
        log_debug(
            f"[ALBUM_PERMISSIONS] Album {album_id} (from collection) has {len(album_members)} members"
        )

    # Fallback: call API directly

    log_debug(
        f"[ALBUM_PERMISSIONS] Album {album_id} (API) has {len(album_members)} members"
    )
    return album_members


@typechecked
def add_members_to_album(*,
            album: AlbumResponseWrapper,
        user:UserResponseWrapper,

    access_level: AlbumUserRole,
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
    response = proxy_add_users_to_album(
        album_id=UUID(album_id),
        client=client,
        body=add_users_dto,
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
        immich_remove_user_from_album.sync_detailed(
            id=UUID(album_id),
            user_id=user_id,
            client=client,
        )
        log_debug(f"[ALBUM_PERMISSIONS] Removed user {user_id} from {album_name}")


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
    album_id = album_wrapper.get_album_uuid()
    album_name = album_wrapper.get_album_name()
    # Use the no-cache UUID accessor when interacting with APIs that expect a UUID
    album_uuid = album_wrapper.get_album_uuid_no_cache()

    report = ModificationReport.get_instance()

    if not resolved_policy.has_match:
        log_debug(f"[ALBUM_PERMISSIONS] Skipping {album_name}: no matching rules")
        return

    # Resolve configured member emails to user IDs
    result = _resolve_emails_to_user_ids(resolved_policy.members, context)
    target_user_ids = set(result.resolved.values())

    # Get current members from API (pass UUID directly)
    # current_members is assigned from _get_current_members, which is defined below. No import needed.
    current_members = _get_current_members(album_uuid, context)
    current_user_ids = {str(member.user.id) for member in current_members}

    # Calculate diff
    users_to_add = target_user_ids - current_user_ids
    users_to_remove = current_user_ids - target_user_ids

    # Phase 2A: PONER (add members)
    if users_to_add:
        add_members_to_album(
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
