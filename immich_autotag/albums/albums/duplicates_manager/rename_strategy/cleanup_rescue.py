"""
Album Cleanup Rescue Operation

This module implements the one-time rescue operation to fix corrupted album names and merge duplicates, as described in the maintenance plan.
Activation is controlled by a config flag. When enabled, only this process runs.
"""

import re
from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper

RENAMED_PATTERN = re.compile(r'(__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM)+')


def cleanup_album_names(album_collection: AlbumCollectionWrapper):
    """
    Identifies albums with corrupted names and attempts to restore their original names.
    Merges duplicate albums as needed.
    """
    for album in album_collection.get_all_albums():
        original_name = _restore_original_name(album.name)
        if original_name != album.name:
            album_collection.rename_album(album, original_name)

    album_collection.merge_duplicate_albums()


def _restore_original_name(name: str) -> str:
    """
    Removes repeated renaming suffixes from album names.
    Example: '2025-11-22-poteo__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM__RENAMED_BY_AUTOTAG_DUPLICATE_USER_ALBUM'
    becomes '2025-11-22-poteo'
    """
    return RENAMED_PATTERN.split(name)[0]


# Entry point for rescue operation

def run_album_cleanup_rescue():
    album_collection = AlbumCollectionWrapper.load_from_db()
    cleanup_album_names(album_collection)
    album_collection.save_to_db()
