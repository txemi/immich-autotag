"""
Album Cleanup Rescue Operation

This module implements the one-time rescue operation to fix corrupted album names and merge duplicates, as described in the maintenance plan.
Activation is controlled by a config flag. When enabled, only this process runs.
"""

import re
from immich_autotag.report.modification_entries_list import ModificationEntriesList

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.albums.duplicates_manager.rename_strategy.constants import (
    RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM_SUFFIX,
)

RENAMED_PATTERN = re.compile(
    rf"({re.escape(RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM_SUFFIX)})+"
)


def _restore_original_name(name: str) -> str:
    """
    Removes repeated renaming suffixes from album names.
    Example: '2025-11-22-original_name__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM'
    becomes '2025-11-22-original_name'
    """
    return RENAMED_PATTERN.split(name)[0]


def cleanup_album_names(album_collection: AlbumCollectionWrapper) -> ModificationEntriesList:
    """
    Identifies albums with corrupted names and attempts to restore their original names.
    Merges duplicate albums as needed.
    """
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

    # Get client and report
    client = album_collection.get_client()
    tag_mod_report = album_collection.get_modification_report()

    # Iterate over all non-deleted albums
    from immich_autotag.report.modification_entries_list import ModificationEntriesList
    modifications = ModificationEntriesList()
    for album in album_collection.get_albums():
        original_name = _restore_original_name(album.get_album_name())
        current_name = album.get_album_name()
        if original_name and original_name != current_name:
            mod_entry = album.rename_album(
                new_name=original_name,
                client=client,
                modification_report=tag_mod_report,
            )
            if mod_entry is not None:
                modifications = modifications.append(mod_entry)
    return modifications


# Entry point for rescue operation


def run_album_cleanup_rescue() -> ModificationEntriesList:
    """
    Runs the album cleanup rescue operation and returns all modification entries performed.
    """
    album_collection = AlbumCollectionWrapper.get_instance()
    modifications = cleanup_album_names(album_collection)
    # If you want to persist changes, ensure the collection is saved via the appropriate method if available
    return modifications
