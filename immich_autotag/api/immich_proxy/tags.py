# ...existing code...
from typing import List
from uuid import UUID

from immich_client.api.tags import create_tag as _create_tag
from immich_client.api.tags import delete_tag as _delete_tag
from immich_client.api.tags import get_all_tags as _get_all_tags
from immich_client.api.tags import get_tag_by_id as _get_tag_by_id
from immich_client.api.tags import tag_assets, untag_assets
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto
from immich_client.models.tag_create_dto import TagCreateDto
from immich_client.models.tag_response_dto import TagResponseDto

from immich_autotag.types import ImmichClient



from immich_autotag.assets.asset_uuid import AssetUUID

def proxy_tag_assets(
    *, tag_id: UUID, client: ImmichClient, asset_ids: List[AssetUUID]
) -> list[BulkIdResponseDto]:
    """Proxy for tag_assets.sync with explicit keyword arguments. Accepts AssetUUIDs."""
    uuid_ids = [a.to_uuid()  for a in asset_ids]
    result = tag_assets.sync(id=tag_id, client=client, body=BulkIdsDto(ids=uuid_ids))
    if result is None:
        raise RuntimeError("tag_assets.sync returned None (unexpected)")
    return result


def proxy_untag_assets(
            *, tag_id: UUID, client: ImmichClient, asset_ids: List[AssetUUID]
) -> list[BulkIdResponseDto]:
    """Proxy for untag_assets.sync with explicit keyword arguments. Accepts AssetUUIDs."""
    uuid_ids = [a.to_uuid() if hasattr(a, 'to_uuid') else a for a in asset_ids]
    result = untag_assets.sync(id=tag_id, client=client, body=BulkIdsDto(ids=uuid_ids))
    if result is None:
        raise RuntimeError("untag_assets.sync returned None (unexpected)")
    return result


def proxy_create_tag(*, client: ImmichClient, name: str):
    """Proxy for create_tag.sync with explicit keyword arguments."""
    tag_create = TagCreateDto(name=name)
    return _create_tag.sync(client=client, body=tag_create)


def proxy_get_all_tags(*, client: ImmichClient):
    """Proxy for get_all_tags.sync with explicit keyword arguments."""
    return _get_all_tags.sync(client=client)


def proxy_delete_tag(*, client: ImmichClient, tag_id: UUID) -> None:
    """Proxy for delete_tag.sync_detailed con resultado parseado."""
    response = _delete_tag.sync_detailed(id=tag_id, client=client)
    return response.parsed


def proxy_get_tag_by_id(*, client: ImmichClient, tag_id: UUID) -> TagResponseDto | None:
    """Proxy for get_tag_by_id.sync with explicit keyword arguments."""
    return _get_tag_by_id.sync(id=tag_id, client=client)
