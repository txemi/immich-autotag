"""
Proxy/fachada para todas las llamadas a la API de assets de Immich.
Este módulo es el ÚNICO punto autorizado para interactuar con immich_client.api.assets.
"""

from uuid import UUID

from immich_client.api.assets import get_asset_info as _get_asset_info
from immich_client.api.assets import update_asset as _update_asset
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.update_asset_dto import UpdateAssetDto

from immich_autotag.types import ImmichClient


def get_asset_info(asset_id: UUID, client: ImmichClient) -> AssetResponseDto | None:
    """
    Wrapper centralizado para get_asset_info.sync.
    """
    return _get_asset_info.sync(id=asset_id, client=client)


def update_asset(
    asset_id: UUID, client: ImmichClient, body: UpdateAssetDto
) -> AssetResponseDto | None:
    """
    Wrapper centralizado para update_asset.sync.
    """
    return _update_asset.sync(id=asset_id, client=client, body=body)
