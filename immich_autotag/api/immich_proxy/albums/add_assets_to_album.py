from immich_client.api.albums import add_assets_to_album
from immich_client.client import AuthenticatedClient
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto

from immich_autotag.api.immich_proxy.debug import (
    format_api_debug_context,
    timed_api_call,
    write_operation_debug,
)
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID


def proxy_add_assets_to_album(
    *, album_id: AlbumUUID, client: AuthenticatedClient, asset_ids: list[AssetUUID]
) -> list[BulkIdResponseDto]:
    # Convert AssetUUIDs to UUIDs for API compatibility

    write_operation_debug()
    uuid_ids = [a.to_uuid() for a in asset_ids]
    context = format_api_debug_context(
        album_id=album_id,
        asset_count=len(asset_ids),
        sample_asset_ids=[str(asset_id) for asset_id in asset_ids[:3]],
    )
    result = timed_api_call(
        operation="add_assets_to_album",
        context=context,
        func=lambda: add_assets_to_album.sync(
            id=album_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
        ),
    )
    if result is None:
        raise RuntimeError(
            f"Failed to add assets to album {album_id}: API returned None"
        )
    return result
