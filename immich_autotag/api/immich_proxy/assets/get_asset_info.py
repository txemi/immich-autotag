import atexit

from immich_client.api.assets import get_asset_info as _get_asset_info
from immich_client.models.asset_response_dto import AssetResponseDto

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.types.client_types import ImmichClient
from immich_autotag.types.uuid_wrappers import AssetUUID

_asset_api_call_count = 0
_asset_api_ids: set[str] = set()


def _print_asset_api_call_summary():
    log(
        f"[DIAG] get_asset_info: total calls={_asset_api_call_count}, unique IDs={len(_asset_api_ids)}",
        level=LogLevel.DEBUG,
    )
    if len(_asset_api_ids) < 30:
        log(f"[DIAG] Unique Asset IDs: {_asset_api_ids}", level=LogLevel.DEBUG)


atexit.register(_print_asset_api_call_summary)


def proxy_get_asset_info(
    asset_id: AssetUUID, client: ImmichClient, use_cache: bool = True
) -> AssetResponseDto | None:
    """
    Centralized wrapper for get_asset_info.sync. Now delegates all cache logic to AssetCacheEntry.
    """
    from immich_autotag.api.immich_proxy.debug import api_debug_breakpoint

    api_debug_breakpoint()
    global _asset_api_call_count
    _asset_api_call_count += 1
    _asset_api_ids.add(str(asset_id))
    # Calls the API directly, without cache logic

    return _get_asset_info.sync(id=asset_id.to_uuid(), client=client)


__all__ = ["AssetResponseDto", "proxy_get_asset_info"]
