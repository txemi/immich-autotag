from immich_client.api.tags import untag_assets
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID, TagUUID
from typing import List

def proxy_untag_assets(
    *, tag_id: TagUUID, client: ImmichClient, asset_ids: List[AssetUUID]
) -> list[BulkIdResponseDto]:
    """Proxy for untag_assets.sync with explicit keyword arguments. Recibe TagUUID y AssetUUIDs."""
    uuid_ids = [a.to_uuid() for a in asset_ids]
    result = untag_assets.sync(
        id=tag_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
    )
    if result is None:
        raise RuntimeError("untag_assets.sync returned None (unexpected)")
    return result

__all__ = ["proxy_untag_assets"]
