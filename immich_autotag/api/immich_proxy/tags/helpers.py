from typing import List

from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto

from immich_autotag.api.immich_proxy.debug import (
    format_api_debug_context,
    timed_api_call,
    write_operation_debug,
)
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID, TagUUID

from .tag_action_enum import TagAction


def proxy_tag_action(
    *,
    tag_id: TagUUID,
    client: ImmichClient,
    asset_ids: List[AssetUUID],
    action: TagAction,
) -> list[BulkIdResponseDto]:
    """
    Generic proxy for tag_assets.sync or untag_assets.sync with explicit keyword arguments.
    action: 'tag' or 'untag'
    """
    from immich_client.api.tags import tag_assets, untag_assets

    write_operation_debug()
    uuid_ids = [a.to_uuid() for a in asset_ids]
    sample_asset_ids = [str(asset_id) for asset_id in asset_ids[:3]]
    context = format_api_debug_context(
        action=action.value,
        tag_id=tag_id,
        asset_count=len(asset_ids),
        sample_asset_ids=sample_asset_ids,
    )
    if action == TagAction.TAG:
        result = timed_api_call(
            operation="tag_assets",
            context=context,
            func=lambda: tag_assets.sync(
                id=tag_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
            ),
        )
    elif action == TagAction.UNTAG:
        result = timed_api_call(
            operation="untag_assets",
            context=context,
            func=lambda: untag_assets.sync(
                id=tag_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
            ),
        )
    else:
        raise ValueError(f"Unknown action: {action}")
    if result is None:
        raise RuntimeError(f"{action}_assets.sync returned None (unexpected)")
    return result


__all__ = ["proxy_tag_action"]
