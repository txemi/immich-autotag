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

from immich_autotag.albums.albums.album_list import AlbumList
from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_report import ModificationReport

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def remove_asset_from_autotag_temporary_albums(
    asset_wrapper: "AssetResponseWrapper",
    temporary_albums: list["AlbumResponseWrapper"],
    tag_mod_report: ModificationReport,
) -> ModificationEntriesList:
    """
    Removes an asset from all temporary autotag albums (albums matching pattern: autotag-temp-unclassified).

    This function is idempotent - calling it multiple times on the same asset/album
    combination has no additional effects after the first removal.

    Cleanup is automatic and always executed. It helps prevent duplicate album memberships
    when assets get classified and no longer need temporary albums.

    """
    removed_album_list = AlbumList()
    modifications = ModificationEntriesList()
    for album_wrapper in temporary_albums:
        # Check if album name matches temporary album pattern
        if not is_temporary_album(album_wrapper.get_album_name()):
            continue
        # Skip if asset not in album (idempotent check)
        if not album_wrapper.has_asset_wrapper(asset_wrapper):
            continue

        client = asset_wrapper.get_context().get_client_wrapper().get_client()

        try:
            # Remove asset from album
            result: ModificationEntry | None = album_wrapper.remove_asset(
                asset_wrapper=asset_wrapper,
                client=client,
                modification_report=tag_mod_report,
            )
            if result is not None:
                # Immediate integrity check: the modification must correspond to the processed album
                if result.album is not album_wrapper:
                    raise RuntimeError(
                        f"Integrity error: modification does not match the processed album. Modification: {result.album}, expected album: {album_wrapper}"
                    )
                removed_album_list.append(album_wrapper)
                modifications.append(result)

            log(
                f"Asset {asset_wrapper.get_id()} removed from temporary album "
                f"{album_wrapper.get_album_name()}",
                level=LogLevel.DEBUG,
            )

        except Exception as e:
            from immich_autotag.config.dev_mode import is_development_mode

            if is_development_mode():
                raise
            log(
                f"Failed to remove asset {asset_wrapper.get_id()} from temporary album {album_wrapper.get_album_name()}: {e}",
                level=LogLevel.IMPORTANT,
            )
            continue

    # Integrity: each modification must correspond to a truly processed album

    mod_album_list = AlbumList(modifications.get_albums()).deduplicate()
    removed_album_list_dedup = removed_album_list.deduplicate()
    if not mod_album_list.equals(removed_album_list_dedup):
        raise RuntimeError(
            f"Integrity error: modifications do not exactly match the processed albums. Modifications: {mod_album_list.to_list()}, albums: {removed_album_list_dedup.to_list()}"
        )

    if not removed_album_list.is_empty():
        album_names = removed_album_list.get_album_names()
        log(
            f"Asset {asset_wrapper.get_id()} cleaned up from {len(album_names)} temporary album(s): {album_names}",
            level=LogLevel.FOCUS,
        )

    return modifications
