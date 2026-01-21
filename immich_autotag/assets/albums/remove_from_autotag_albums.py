"""Helper function to remove assets from temporary autotag-generated albums.

This module provides functionality to remove an asset from all temporary autotag albums
when it gets classified. Useful for cleaning up temporary album assignments to avoid
duplicate album memberships.

This cleanup is automatic and always enabled - it helps prevent duplicate album memberships
when assets transition from unclassified to classified state.

Uses centralized temporary album pattern from temporary_albums module to ensure
consistency between creation and removal operations.
"""

from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.assets.albums.temporary_albums import is_temporary_album
from immich_autotag.config._internal_types import ErrorHandlingMode
from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def remove_asset_from_autotag_temporary_albums(
    asset_wrapper: "AssetResponseWrapper",
    temporary_albums: list["AlbumResponseWrapper"],
    tag_mod_report: ModificationReport,
) -> list[str]:
    """
    Removes an asset from all temporary autotag albums (albums matching pattern: autotag-temp-unclassified).

    This function is idempotent - calling it multiple times on the same asset/album
    combination has no additional effects after the first removal.

    Cleanup is automatic and always executed. It helps prevent duplicate album memberships
    when assets get classified and no longer need temporary albums.

    """
    removed_album_names: list[str] = []

    for album_wrapper in temporary_albums:
        # Check if album name matches temporary album pattern
        if not is_temporary_album(album_wrapper.get_album_name()):
            continue

        # Skip if asset not in album (idempotent check)
        if not album_wrapper.has_asset(asset_wrapper.asset):
            continue

        try:
            client = asset_wrapper.context.client
        except Exception:
            from immich_autotag.context.immich_context import ImmichContext

            client = ImmichContext.get_default_client()

        try:
            # Remove asset from album
            album_wrapper.remove_asset(
                asset_wrapper=asset_wrapper,
                client=client,
                tag_mod_report=tag_mod_report,
            )
            removed_album_names.append(album_wrapper.get_album_name())

            log(
                f"Asset {asset_wrapper.id} removed from temporary album {album_wrapper.get_album_name()}",
                level=LogLevel.DEBUG,
            )

        except Exception as e:
            # <-- HERE the message '[WARNING] Failed to remove asset ...' is printed if an error occurs while removing the asset from the temporary album.
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise
            log(
                f"Failed to remove asset {asset_wrapper.id} from temporary album {album_wrapper.get_album_name()}: {e}",
                level=LogLevel.IMPORTANT,
            )
            # Continue processing other albums even if one fails
            continue

    if removed_album_names:
        log(
            f"Asset {asset_wrapper.id} cleaned up from {len(removed_album_names)} temporary album(s): {removed_album_names}",
            level=LogLevel.FOCUS,
        )

    return removed_album_names
