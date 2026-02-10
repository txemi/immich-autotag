
from typeguard import typechecked
from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.report.modification_entries_list import ModificationEntriesList

from immich_autotag.albums.album.album_response_wrapper import (
    AlbumResponseWrapper,
)
from immich_autotag.albums.duplicates.asset_move import (
    MoveAssetsResult,
    move_assets_between_albums,
)
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.client_types import ImmichClient


@typechecked
def merge_duplicate_albums(
    *,
    collection: AlbumCollectionWrapper,
    duplicate_album: AlbumResponseWrapper,
    target_album: AlbumResponseWrapper,
    client: ImmichClient,
    tag_mod_report: ModificationReport,
) -> ModificationEntriesList:
    """
    Merge all assets from the duplicate album into the target album,
    then delete the duplicate album from the collection and server.
    """

    # Safety: Ensure duplicate_album is actually a duplicate before proceeding
    if not duplicate_album.is_duplicate_album():
        raise RuntimeError(
            "Refusing to merge/delete album '",
            f"{duplicate_album.get_album_name()}' (id=",
            f"{duplicate_album.get_album_uuid()}): not a duplicate album.",
        )

    # Move assets from duplicate to target
    modifications = move_assets_between_albums(
        collection=collection,
        dest=target_album,
        src=duplicate_album,
        client=client,
        tag_mod_report=tag_mod_report,
    )
    # Remove duplicate album from server and collection, collect modification entry
    delete_mod = collection.delete_album(
        wrapper=duplicate_album,
        client=client,
        tag_mod_report=tag_mod_report,
        reason="Merged and deleted duplicate album",
    )
    # Combine all modifications into a single ModificationEntriesList
    from immich_autotag.report.modification_entries_list import ModificationEntriesList
    combined_mods = modifications.append(delete_mod)
    return combined_mods
