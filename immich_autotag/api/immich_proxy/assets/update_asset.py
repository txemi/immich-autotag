from immich_client.api.assets import update_asset as _update_asset
from immich_client.models.update_asset_dto import UpdateAssetDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID

def proxy_update_asset(
    asset_id: AssetUUID, client: ImmichClient, body: UpdateAssetDto
) -> AssetResponseDto | None:
    """
    Centralized wrapper for update_asset.sync.
    """
    return _update_asset.sync(id=asset_id.to_uuid(), client=client, body=body)
