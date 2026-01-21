from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.duplicates.mover import move_assets_between_albums
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient


@typechecked
def merge_duplicate_albums(
    collection: "AlbumCollectionWrapper",
    duplicate_album: AlbumResponseWrapper,
    target_album: AlbumResponseWrapper,
    client: ImmichClient,
    tag_mod_report: ModificationReport,
) -> AlbumResponseWrapper:
    """
    Merge all assets from the duplicate album into the target album,
    then delete the duplicate album from the collection and server.
    """

    # Safety: Ensure duplicate_album is actually a duplicate before proceeding
    if not duplicate_album.is_duplicate_album():
        raise RuntimeError(
            f"Refusing to merge/delete album '{duplicate_album.get_album_name()}' (id={duplicate_album.get_album_id()}): not a duplicate album."
        )

    # Move assets from duplicate to target
    move_assets_between_albums(
        collection=collection,
        dest=target_album,
        src=duplicate_album,
        client=client,
        tag_mod_report=tag_mod_report,
    )
    # Remove duplicate album from server and collection
    collection.delete_album(
        wrapper=duplicate_album,
        client=client,
        tag_mod_report=tag_mod_report,
        reason="Merged and deleted duplicate album",
    )

    # ...existing code...

    # Return the surviving album for convenience
    return target_album
