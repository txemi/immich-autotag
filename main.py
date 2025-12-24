from __future__ import annotations

# --- Detailed classification result ---
# NOTE: With 'from __future__ import annotations' you can use types defined later in annotations,
# but for attrs validators the type must be defined before or validated in __attrs_post_init__.
from typing import TYPE_CHECKING

from immich_client import Client
from immich_client.api.albums import get_all_albums, get_album_info, update_album_info
from immich_client.api.assets import get_asset_info
from immich_client.api.search import search_assets
from immich_client.api.tags import get_all_tags
from immich_client.models import MetadataSearchDto
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from typeguard import typechecked

# ==================== INTERNAL VARIABLES (DO NOT EDIT) ====================
# Ahora centralizadas en immich_autotag/config.py
from immich_autotag.config import (
    IMMICH_BASE_URL,
)
from immich_autotag.core.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.core.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.core.immich_context import ImmichContext
from immich_autotag.core.tag_collection_wrapper import TagCollectionWrapper
# ==================== USER-EDITABLE CONFIGURATION ====================
# All user configuration is now in a separate module for clarity and maintainability.
from immich_autotag.immich_user_config import *

from immich_autotag.utils.print_tags import print_tags
from immich_autotag.utils.process_assets import process_assets

# ==================== TAG MODIFICATION TRACE REPORT ====================

if TYPE_CHECKING:
    from .ejemplo_immich_client import ImmichContext


@typechecked
def list_albums(client: Client) -> AlbumCollectionWrapper:
    """
    Returns the collection of extended albums (wrappers) encapsulated in AlbumCollectionWrapper.
    """
    albums = get_all_albums.sync(client=client)
    albums_full: list[AlbumResponseWrapper] = []
    print("\nAlbums:")
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
            album_full.album_name = cleaned_name
        albums_full.append(AlbumResponseWrapper(album=album_full))
    print(f"Total albums: {len(albums_full)}\n")
    MIN_ALBUMS = 326
    if len(albums_full) < MIN_ALBUMS:
        raise Exception(
            f"ERROR: Unexpectedly low number of albums: {len(albums_full)} < {MIN_ALBUMS}"
        )
    return AlbumCollectionWrapper(albums=albums_full)


@typechecked
def list_tags(client: Client) -> TagCollectionWrapper:
    tag_collection = TagCollectionWrapper.from_api(client)
    print_tags(tag_collection.tags)
    return tag_collection


def main():
    client = Client(base_url=IMMICH_BASE_URL, headers={"x-api-key": API_KEY})
    tag_collection = list_tags(client)
    albums_collection = list_albums(client)
    context = ImmichContext(
        client=client,
        albums_collection=albums_collection,
        tag_collection=tag_collection,
    )

    # You can change the max_assets value here or pass it as an external argument
    max_assets = None
    process_assets(context, max_assets=max_assets)


if __name__ == "__main__":
    main()
