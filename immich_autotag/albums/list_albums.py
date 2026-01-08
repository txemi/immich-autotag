from __future__ import annotations

from immich_client import Client
from immich_client.api.albums import get_album_info, get_all_albums, update_album_info
from immich_client.models.update_album_dto import UpdateAlbumDto
from typeguard import typechecked

from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper


@typechecked
def list_albums(client: Client) -> AlbumCollectionWrapper:
    """
    Returns the collection of extended albums (wrappers) encapsulated in AlbumCollectionWrapper.
    """
    return AlbumCollectionWrapper.from_client(client)
