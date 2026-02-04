from immich_autotag.types.client_types import ImmichClient
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.context.context import ImmichContext


def _is_temp_album(album: AlbumResponseWrapper) -> bool:
    """
    Returns True if the album is considered temporary.
    The logic for 'temporary' should match the codebase conventions (e.g., name pattern, tag, etc).
    """
    # Example: albums with names starting with 'temp_' or a specific tag
    name = album.get_name()
    return name.startswith("temp_") or album.has_tag("temporary")


def _is_album_healthy(album: AlbumResponseWrapper) -> bool:
    """
    Returns True if the album is considered healthy.
    The health check logic should match the codebase conventions (e.g., not broken, not empty, etc).
    """
    # Example: album must have assets and not be marked as broken
    if album.is_broken():
        return False
    if album.get_asset_count() == 0:
        return False
    return True


def _delete_album(album: AlbumResponseWrapper, client: ImmichClient) -> None:
    """
    Deletes the album using the API.
    """
    from immich_autotag.api.logging_proxy.albums import logging_delete_album
    logging_delete_album(client=client, album=album)


def delete_unhealthy_temp_albums(context: ImmichContext) -> int:
    """
    Iterates all albums, finds temporary ones, checks health, and deletes those that are unhealthy.
    Returns the number of deleted albums.
    """
    client = context.get_client()
    album_manager = context.get_album_manager()
    albums = album_manager.get_all_albums()
    count = 0
    for album in albums:
        if _is_temp_album(album) and not _is_album_healthy(album):
            _delete_album(album, client)
            count += 1
    return count
