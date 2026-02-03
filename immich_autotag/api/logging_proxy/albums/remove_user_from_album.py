"""
Logging proxy for removing members from albums.

Wraps remove member functions to add automatic event logging,
statistics tracking, and modification reporting.

This layer receives rich wrapper objects (AlbumResponseWrapper, UserResponseWrapper)
instead of raw IDs. This ensures robust, type-safe operations with full
context available for event tracking and error handling.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from typeguard import typechecked

from immich_autotag.api.immich_proxy.albums import proxy_remove_user_from_album
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.utils import log_debug
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper


@typechecked
def _remove_members_from_album(
    *,
    album: "AlbumResponseWrapper",
    members: Sequence["UserResponseWrapper"],
    context: ImmichContext,
) -> None:
    """
    [INTERNAL] Remove users from album using the API. No event logging.

    Solo para uso interno de logging_proxy. No registra eventos ni logs de auditoria.
    No debe ser llamada directamente desde fuera de este modulo.
    """
    album_id = album.get_album_uuid()
    album_name = album.get_album_name()
    client = context.get_client_wrapper().get_client()
    for member in members:
        user_id = member.get_uuid()
        proxy_remove_user_from_album(client=client, album_id=album_id, user_id=user_id)
        log_debug(f"[ALBUM_PERMISSIONS] Removed user {user_id} from {album_name}")


@typechecked
def logging_remove_members_from_album(
    *,
    album: "AlbumResponseWrapper",
    members: list["UserResponseWrapper"],
    context: ImmichContext,
    matched_rules: Optional[list[str]] = None,
    groups: Optional[list[str]] = None,
) -> None:
    """
    Remove members from album with automatic event logging.

    Args:
        album: Album wrapper with album data
        members: List of UserResponseWrapper objects to remove
        context: ImmichContext with API client
        matched_rules: Optional list of rule names that triggered this action
        groups: Optional list of group names involved

    Side effects:
        - Calls the API to remove members from the album
        - Records the event in ModificationReport
        - Updates statistics (delegated to ModificationReport)
    """
    # Call the underlying function
    _remove_members_from_album(
        album=album,
        members=members,
        context=context,
    )

    # Record the event in the modification report
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    report.add_album_permission_modification(
        kind=ModificationKind.ALBUM_PERMISSION_REMOVED,
        album=album,
        matched_rules=matched_rules,
        groups=groups,
        members=members,
        access_level=None,
    )
