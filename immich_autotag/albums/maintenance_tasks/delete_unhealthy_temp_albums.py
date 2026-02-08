from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.types.client_types import ImmichClient


def _delete_album(
    album: AlbumResponseWrapper, client: ImmichClient, albums_collection
) -> None:
    """
    Deletes the album using the AlbumCollectionWrapper API.
    """
    from immich_autotag.report.modification_report import ModificationReport

    tag_mod_report = ModificationReport.get_instance()
    albums_collection.delete_album(
        wrapper=album,
        client=client,
        tag_mod_report=tag_mod_report,
        reason="Unhealthy temporary album deleted automatically",
    )


def delete_unhealthy_temp_albums(context: ImmichContext) -> int:
    """
    Iterates all albums, finds temporary ones, checks health, and deletes those that are unhealthy.
    Returns the number of deleted albums.
    """
    client = context.get_client_wrapper().get_client()
    albums_collection = context.get_albums_collection()
    albums = albums_collection.get_albums()
    count = 0

    from immich_autotag.assets.albums.temporary_manager.health import (
        is_temporary_album_healthy,
    )

    for album in albums:
        if album.is_temporary_album() and not is_temporary_album_healthy(album):
            _delete_album(album, client, albums_collection)
            log(
                f"[PROGRESS] [ALBUM-DELETE] Deleted unhealthy temporary album: '{album.get_album_name()}' (UUID: {album.get_album_uuid()})",
                level=LogLevel.PROGRESS,
            )
            count += 1

    if count > 0:
        log(
            f"[MAINTENANCE] Deleted {count} unhealthy temporary albums (reason: not healthy, e.g. assets too far apart in time or empty)",
            level=LogLevel.PROGRESS,
        )
    else:
        log(
            "[MAINTENANCE] No unhealthy temporary albums found for deletion.",
            level=LogLevel.PROGRESS,
        )
    return count
