from immich_client.api.tags import get_all_tags as _get_all_tags

from immich_autotag.types.client_types import ImmichClient


def proxy_get_all_tags(*, client: ImmichClient):
    """Proxy for get_all_tags.sync with explicit keyword arguments."""
    return _get_all_tags.sync(client=client)


__all__ = ["proxy_get_all_tags"]
