# --- Diagnóstico de llamadas a la API de assets ---
import atexit

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

_asset_api_call_count = 0
_asset_api_ids: set[str] = set()


def _print_asset_api_call_summary():
    log(
        f"[DIAG] get_asset_info: llamadas totales={_asset_api_call_count}, IDs únicos={len(_asset_api_ids)}",
        level=LogLevel.DEBUG,
    )
    if len(_asset_api_ids) < 30:
        log(f"[DIAG] Asset IDs únicos: {_asset_api_ids}", level=LogLevel.DEBUG)


atexit.register(_print_asset_api_call_summary)
"""
Proxy/fachada para todas las llamadas a la API de assets de Immich.
Este módulo es el ÚNICO punto autorizado para interactuar con immich_client.api.assets.
"""

from uuid import UUID

from immich_client.api.assets import get_asset_info as _get_asset_info
from immich_client.api.assets import update_asset as _update_asset
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_autotag.utils.api_disk_cache import get_entity_from_cache, save_entity_to_cache
from immich_client.models.update_asset_dto import UpdateAssetDto

from immich_autotag.types import ImmichClient


def get_asset_info(asset_id: UUID, client: ImmichClient, use_cache: bool = True) -> AssetResponseDto | None:
    """
    Wrapper centralizado para get_asset_info.sync. Incluye diagnóstico de llamadas y caché en disco.
    """
    global _asset_api_call_count, _asset_api_ids
    _asset_api_call_count += 1
    _asset_api_ids.add(str(asset_id))
    # Buscar en caché
    cache_data = get_entity_from_cache("assets", str(asset_id), use_cache=use_cache)
    if cache_data is not None:
        # Reconstruir el DTO desde dict
        return AssetResponseDto.from_dict(cache_data)
    # Si no está en caché, llamar a la API
    dto = _get_asset_info.sync(id=asset_id, client=client)
    if dto is not None:
        # Guardar en caché como dict
        save_entity_to_cache("assets", str(asset_id), dto.to_dict())
    return dto


def update_asset(
    asset_id: UUID, client: ImmichClient, body: UpdateAssetDto
) -> AssetResponseDto | None:
    """
    Wrapper centralizado para update_asset.sync.
    """
    return _update_asset.sync(id=asset_id, client=client, body=body)
