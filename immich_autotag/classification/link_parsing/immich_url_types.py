from typing import NamedTuple, Optional
from uuid import UUID


class ImmichUrlUuids(NamedTuple):
    album_uuid: Optional[UUID]
    asset_uuid: Optional[UUID]
