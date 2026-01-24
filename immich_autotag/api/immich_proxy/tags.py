from typing import List
from uuid import UUID

from immich_client import Client
from immich_client.api.tags import tag_assets, untag_assets
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto


def proxy_tag_assets(
    *, tag_id: UUID, client: Client, asset_ids: List[UUID]
) -> list[BulkIdResponseDto]:
    """Proxy for tag_assets.sync with explicit keyword arguments."""
    return tag_assets.sync(id=tag_id, client=client, body=BulkIdsDto(ids=asset_ids))


def proxy_untag_assets(
    *, tag_id: UUID, client: Client, asset_ids: List[UUID]
) -> list[BulkIdResponseDto]:
    """Proxy for untag_assets.sync with explicit keyword arguments."""
    return untag_assets.sync(id=tag_id, client=client, body=BulkIdsDto(ids=asset_ids))
