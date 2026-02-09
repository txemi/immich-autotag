"""
Renaming strategy for duplicate albums.

This module provides a function to rename duplicate albums according to the rescue and renaming policy.
"""
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.report.modification_report import ModificationReport


def rename_duplicate_album(album_wrapper, client: ImmichClient, tag_mod_report: ModificationReport):
    """
    Renames a duplicate album by appending the rescue suffix.
    """
    new_name = f"{album_wrapper.get_album_name()}__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM"
    album_wrapper.rename_album(new_name, client, tag_mod_report)
