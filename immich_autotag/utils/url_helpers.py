from __future__ import annotations

import uuid
from urllib.parse import ParseResult, urlparse

from typeguard import typechecked

from immich_autotag.config.host_config import (
    IMMICH_PHOTO_PATH_TEMPLATE,
    get_immich_web_base_url,
)
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID


def get_immich_photo_url(asset_id: AssetUUID) -> ParseResult:
    """
    Returns the Immich web URL for an asset given its id (AssetUUID) as ParseResult.
    """
    if not isinstance(asset_id, AssetUUID):
        raise TypeError(f"asset_id must be AssetUUID, not {type(asset_id)}")
    asset_id_str = str(asset_id)
    url = (
        f"{get_immich_web_base_url()}"
        f"{IMMICH_PHOTO_PATH_TEMPLATE.format(id=asset_id_str)}"
    )
    return urlparse(url)


@typechecked
def get_immich_album_url(album_id: AlbumUUID) -> ParseResult:
    """
    Returns the Immich web URL for an album given its id (UUID) as ParseResult.
    """
    # AlbumUUID is a wrapper, extract the internal uuid.UUID
    uuid_value = album_id.to_uuid() 
    url = f"{get_immich_web_base_url()}/albums/{str(uuid_value)}"
    return urlparse(url)
