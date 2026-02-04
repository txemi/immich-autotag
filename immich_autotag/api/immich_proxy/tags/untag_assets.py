from typing import List

from immich_autotag.api.immich_proxy.tags.helpers import proxy_tag_action
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID, TagUUID


def proxy_untag_assets(
    *, tag_id: TagUUID, client: ImmichClient, asset_ids: List[AssetUUID]
):
    """Proxy for untag_assets.sync with explicit keyword arguments. Uses generic helper."""
    from .tag_action_enum import TagAction

    return proxy_tag_action(
        tag_id=tag_id, client=client, asset_ids=asset_ids, action=TagAction.UNTAG
    )


__all__ = ["proxy_untag_assets"]
