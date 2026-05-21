"""
Logging proxy for updating an album user's role (drift correction).

Used by the sync pipeline when an existing albumUser has a role that differs
from the role expected by the matching AlbumSelectionRule. Follows the same
pattern as remove_user_from_album: receives wrapper objects, calls the proxy,
records the change in ModificationReport.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from typeguard import typechecked

from immich_autotag.api.immich_proxy.albums import proxy_update_album_user
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log_debug
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_client.models.album_user_role import AlbumUserRole

    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper


@typechecked
def _update_members_role(
    *,
    album: "AlbumResponseWrapper",
    members: Sequence["UserResponseWrapper"],
    role: "AlbumUserRole",
    context: ImmichContext,
) -> None:
    """
    [INTERNAL] Update each member's role in the album. No event logging.
    """
    album_id = album.get_album_uuid()
    album_name = album.get_album_name()
    client = context.get_client_wrapper().get_client()
    for member in members:
        user_id = member.get_uuid()
        proxy_update_album_user(
            client=client, album_id=album_id, user_id=user_id, role=role
        )
        log_debug(
            f"[ALBUM_PERMISSIONS] Updated role of user {user_id} in {album_name} -> {role.value}"
        )


@typechecked
def logging_update_members_role(
    *,
    album: "AlbumResponseWrapper",
    members: list["UserResponseWrapper"],
    role: "AlbumUserRole",
    context: ImmichContext,
    matched_rules: Optional[list[str]] = None,
    groups: Optional[list[str]] = None,
) -> None:
    """
    Update the role of multiple members of an album, with automatic event logging.
    """
    _update_members_role(
        album=album,
        members=members,
        role=role,
        context=context,
    )

    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    report.add_album_permission_modification(
        kind=ModificationKind.ALBUM_PERMISSION_ROLE_CHANGED,
        album=album,
        matched_rules=matched_rules,
        groups=groups,
        members=members,
        access_level=role,
    )
