from __future__ import annotations

from typeguard import typechecked

from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.types import ImmichClient


@typechecked
def list_albums(client: ImmichClient) -> AlbumCollectionWrapper:
    """
    Returns the collection of extended albums (wrappers) encapsulated in AlbumCollectionWrapper.
    """
    return AlbumCollectionWrapper.from_client(client)
