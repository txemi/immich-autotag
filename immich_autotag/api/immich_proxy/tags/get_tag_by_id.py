from immich_client.api.tags import get_tag_by_id as _get_tag_by_id
from immich_client.models.tag_response_dto import TagResponseDto
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import TagUUID

def proxy_get_tag_by_id(
    *, client: ImmichClient, tag_id: TagUUID
) -> TagResponseDto | None:
    """Proxy for get_tag_by_id.sync with explicit keyword arguments."""
    return _get_tag_by_id.sync(id=tag_id.to_uuid(), client=client)

__all__ = ["proxy_get_tag_by_id"]
