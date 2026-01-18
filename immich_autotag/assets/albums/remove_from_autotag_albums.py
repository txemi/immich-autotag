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
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport

if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
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

    Args:
        asset_wrapper: The asset to remove from temporary albums.
        temporary_albums: List of album wrappers to check for removal.
        tag_mod_report: ModificationReport to track the removal operations (required).

    Returns:
        A list of album names from which the asset was successfully removed.

    Example:
        >>> removed_albums = remove_asset_from_autotag_temporary_albums(
        ...     asset_wrapper=my_asset,
        ...     temporary_albums=all_albums,
        ...     tag_mod_report=report
        ... )
        >>> print(f"Removed from: {removed_albums}")
        Removed from: ['2024-01-15-autotag-temp-unclassified', '2024-01-16-autotag-temp-unclassified']
    """
    removed_album_names = []

    for album_wrapper in temporary_albums:
        # Check if album name matches temporary album pattern
        if not is_temporary_album(album_wrapper.album.name):
            continue

        # Skip if asset not in album (idempotent check)
        if not album_wrapper.has_asset(asset_wrapper.asset):
            continue

        try:
            # Remove asset from album
            album_wrapper.remove_asset(
                asset_wrapper=asset_wrapper,
                client=asset_wrapper.client,
                tag_mod_report=tag_mod_report,
            )
            removed_album_names.append(album_wrapper.album.name)

            log(
                f"Asset {asset_wrapper.id} removed from temporary album {album_wrapper.album.name}",
                level=LogLevel.DEBUG,
            )

        except Exception as e:
            log(
                f"Failed to remove asset {asset_wrapper.id} from temporary album {album_wrapper.album.name}: {e}",
                level=LogLevel.WARNING,
            )
            # Continue processing other albums even if one fails
            continue

    if removed_album_names:
        log(
            f"Asset {asset_wrapper.id} cleaned up from {len(removed_album_names)} temporary album(s): {removed_album_names}",
            level=LogLevel.FOCUS,
        )

    return removed_album_names
