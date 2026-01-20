from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper

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
) -> None:
    """
    Merge all assets from the duplicate album into the target album,
    then delete the duplicate album from the collection and server.
    """
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

    if tag_mod_report:
        from immich_autotag.tags.modification_kind import ModificationKind

        tag_mod_report.add_album_modification(
            kind=ModificationKind.DELETE_ALBUM,
            album=duplicate_album,
            old_value=duplicate_album.get_album_name(),
            extra={"reason": "Merged and deleted duplicate album"},
        )
