from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


def deduplicate_albums_by_id(
    albums: list["AlbumResponseWrapper"],
) -> list["AlbumResponseWrapper"]:
    """
    Given a list of AlbumResponseWrapper, return a list with unique albums by uuid (as string).
    """
    seen_ids: set[str] = set()
    unique_albums: list["AlbumResponseWrapper"] = []
    for album in albums:
        album_id: str = str(album.get_album_uuid())
        if album_id not in seen_ids:
            seen_ids.add(album_id)
            unique_albums.append(album)
    return unique_albums
