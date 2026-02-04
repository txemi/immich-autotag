from immich_autotag.types.client_types import ImmichClient
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.context.immich_context import ImmichContext



def _is_temp_album(album: AlbumResponseWrapper) -> bool:
    """
    Returns True if the album is considered temporary (project standard logic).
    """
    return album.is_temporary_album()



def _is_album_healthy(album: AlbumResponseWrapper) -> bool:
    """
    Returns True if the album is considered healthy (project standard logic).
    """
    from immich_autotag.assets.albums.temporary_manager.health import is_temporary_album_healthy
    return is_temporary_album_healthy(album)


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
    client = context.get_client_wrapper().get_client()
    album_manager = context.get_album_manager()
    albums = album_manager.get_all_albums()
    count = 0
    for album in albums:
        if _is_temp_album(album) and not _is_album_healthy(album):
            _delete_album(album, client)
            count += 1
    return count
