from typing import NamedTuple, Optional

from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID


class ImmichUrlUuids(NamedTuple):
    album_uuid: Optional[AlbumUUID]
    asset_uuid: Optional[AssetUUID]
