"""
Utility to find duplicate album names in the collection.
"""

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper


def find_duplicate_album_names(collection: AlbumCollectionWrapper) -> list[str]:
    name_count: dict[str, int] = {}
    for album in collection.get_albums():
        name = album.get_album_name()
        name_count[name] = name_count.get(name, 0) + 1
    duplicates = [name for name, count in name_count.items() if count > 1]
    return duplicates
