"""
Renaming strategy for duplicate albums.

This module provides a function to rename duplicate albums according to the rescue and renaming policy.
"""

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.duplicates_manager.rename_strategy.constants import (
    RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM_SUFFIX,
)
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.client_types import ImmichClient


def rename_duplicate_album(
    album_wrapper: AlbumResponseWrapper,
    client: ImmichClient,
    tag_mod_report: ModificationReport,
) -> "ModificationEntry | None":
    """
    Renames a duplicate album by appending the rescue suffix.
    """
    new_name = f"{album_wrapper.get_album_name()}{RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM_SUFFIX}"
    return album_wrapper.rename_album(
        new_name=new_name,
        client=client,
        modification_report=tag_mod_report,
    )
