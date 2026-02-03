from typing import List

from immich_client.api.tags import tag_assets
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto

from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID, TagUUID


def proxy_tag_assets(
    *, tag_id: TagUUID, client: ImmichClient, asset_ids: List[AssetUUID]
) -> list[BulkIdResponseDto]:
    """Proxy for tag_assets.sync with explicit keyword arguments. Recibe TagUUID y AssetUUIDs."""
    uuid_ids = [a.to_uuid() for a in asset_ids]
    result = tag_assets.sync(
        id=tag_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
    )
    if result is None:
        raise RuntimeError("tag_assets.sync returned None (unexpected)")
    return result
