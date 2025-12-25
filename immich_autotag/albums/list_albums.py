from __future__ import annotations

from immich_client import Client
from immich_client.api.albums import get_all_albums, get_album_info, update_album_info
from immich_client.models.update_album_dto import UpdateAlbumDto
from typeguard import typechecked

from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper


@typechecked
def list_albums(client: Client) -> AlbumCollectionWrapper:
    """
    Returns the collection of extended albums (wrappers) encapsulated in AlbumCollectionWrapper.
    """
    albums = get_all_albums.sync(client=client)
    albums_full: list[AlbumResponseWrapper] = []
    print("\nAlbums:")
    from immich_autotag.tags.tag_modification_report import TagModificationReport
    tag_mod_report = TagModificationReport.get_instance()
    for album in albums:
        album_full = get_album_info.sync(id=album.id, client=client)
        n_assets = len(album_full.assets) if album_full.assets else 0
        print(f"- {album_full.album_name} (assets: {n_assets})")
        if album_full.album_name.startswith(" "):
            cleaned_name = album_full.album_name.strip()
            update_body = UpdateAlbumDto(album_name=cleaned_name)
            update_album_info.sync(
                id=album_full.id,
                client=client,
                body=update_body,
            )
            print(f"Renamed album '{album_full.album_name}' to '{cleaned_name}'")
            # Log renaming
            tag_mod_report.add_album_modification(
                action="rename",
                album_id=album_full.id,
                album_name=cleaned_name,
                old_name=album_full.album_name,
                new_name=cleaned_name,
            )
            album_full.album_name = cleaned_name
        albums_full.append(AlbumResponseWrapper(album=album_full))
    tag_mod_report.flush()
    print(f"Total albums: {len(albums_full)}\n")
    MIN_ALBUMS = 326
    if len(albums_full) < MIN_ALBUMS:
        raise Exception(
            f"ERROR: Unexpectedly low number of albums: {len(albums_full)} < {MIN_ALBUMS}"
        )
    return AlbumCollectionWrapper(albums=albums_full)
