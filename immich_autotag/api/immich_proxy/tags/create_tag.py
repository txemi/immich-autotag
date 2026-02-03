from immich_client.api.tags import create_tag as _create_tag
from immich_client.models.tag_create_dto import TagCreateDto

from immich_autotag.types.client_types import ImmichClient


def proxy_create_tag(*, client: ImmichClient, name: str):
    """Proxy for create_tag.sync with explicit keyword arguments."""
    tag_create = TagCreateDto(name=name)
    return _create_tag.sync(client=client, body=tag_create)


__all__ = ["proxy_create_tag"]
