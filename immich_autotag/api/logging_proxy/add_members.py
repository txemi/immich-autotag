"""
Logging proxy for adding members to albums.

Wraps add member functions to add automatic event logging,
statistics tracking, and modification reporting.

This layer receives rich wrapper objects (AlbumResponseWrapper, UserResponseWrapper)
instead of raw IDs. This ensures robust, type-safe operations with full
context available for event tracking and error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_role import AlbumUserRole
from typeguard import typechecked

from immich_autotag.api.immich_proxy.albums import proxy_add_users_to_album
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper


@typechecked
def add_members_to_album(
    *,
    album: "AlbumResponseWrapper",
    users: List["UserResponseWrapper"],
    access_level: AlbumUserRole,
    context: ImmichContext,
) -> None:
    """
    Add members to album (PONER).

    Low-level function that calls the API directly.
    For operations that need automatic logging, use logging_add_members_to_album instead.
    """
    album_id = album.get_album_uuid()
    album_name = album.get_album_name()
    user_ids = [user.get_uuid() for user in users]

    log(
        f"[ALBUM_PERMISSIONS] Adding {len(user_ids)} members to {album_name} "
        f"(access: {access_level})",
        level=LogLevel.PROGRESS,
    )

    # Build AddUsersDto
    album_users_dto = [
        AlbumUserAddDto(
            user_id=user_id.to_uuid(),
            role=access_level,
        )
        for user_id in user_ids
    ]
    add_users_dto = AddUsersDto(album_users=album_users_dto)

    # Call API
    client_wrapper = context.get_client_wrapper()
    client = client_wrapper.get_client()
    response = proxy_add_users_to_album(
        album_id=album_id,
        client=client,
        body=add_users_dto,
    )
    if response is not None:
        log_debug(
            f"[ALBUM_PERMISSIONS] Successfully added {len(user_ids)} "
            f"members to {album_name}"
        )


@typechecked
def logging_add_members_to_album(
    *,
    album: "AlbumResponseWrapper",
    members: list["UserResponseWrapper"],
    access_level: AlbumUserRole,
    context: ImmichContext,
    matched_rules: Optional[list[str]] = None,
    groups: Optional[list[str]] = None,
) -> None:
    """
    Add members to album with automatic event logging.

    Args:
        album: Album wrapper with album data
        members: List of UserResponseWrapper objects to add
        access_level: Permission level (AlbumUserRole enum)
        context: ImmichContext with API client
        matched_rules: Optional list of rule names that triggered this action
        groups: Optional list of group names involved

    Side effects:
        - Calls the API to add members to the album
        - Records the event in ModificationReport
        - Updates statistics (delegated to ModificationReport)
    """
    # Call the underlying function
    add_members_to_album(
        album=album,
        users=members,
        access_level=access_level,
        context=context,
    )

    # Record the event in the modification report
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    report.add_album_permission_modification(
        kind=ModificationKind.ALBUM_PERMISSION_SHARED,
        album=album,
        matched_rules=matched_rules,
        groups=groups,
        members=members,
        access_level=access_level,
    )


@typechecked
def logging_add_user_to_album(
    *,
    album: "AlbumResponseWrapper",
    user: "UserResponseWrapper",
    access_level: AlbumUserRole,
    context: ImmichContext,
) -> None:
    """
    Add a single user to album with automatic event logging.

    This is for manual user addition (e.g., when creating albums),
    not rule-based permission sharing. Uses ADD_USER_TO_ALBUM event.

    Args:
        album: Album wrapper with album data
        user: UserResponseWrapper object to add
        access_level: Permission level (AlbumUserRole enum)
        context: ImmichContext with API client

    Side effects:
        - Calls the API to add the user to the album
        - Records ADD_USER_TO_ALBUM event in ModificationReport
    """
    # Call the underlying function
    add_members_to_album(
        album=album,
        users=[user],
        access_level=access_level,
        context=context,
    )

    # Record the event in the modification report
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    report.add_album_modification(
        kind=ModificationKind.ADD_USER_TO_ALBUM,
        album=album,
        extra={"added_user": str(user.get_uuid())},
    )
