from immich_client.api.tags import delete_tag as _delete_tag
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import TagUUID

def proxy_delete_tag(*, client: ImmichClient, tag_id: TagUUID) -> None:
    """Proxy for delete_tag.sync_detailed con resultado parseado."""
    _delete_tag.sync_detailed(id=tag_id.to_uuid(), client=client)
    # response.parsed is None for delete operations

__all__ = ["proxy_delete_tag"]
