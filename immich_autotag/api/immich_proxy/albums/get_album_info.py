from __future__ import annotations

import atexit
from typing import Any, Callable, List, Optional

from immich_client.api.albums import (
    add_assets_to_album,
    get_album_info,
    get_all_albums,
    remove_asset_from_album,
    update_album_info,
)
from immich_client.client import AuthenticatedClient
from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from immich_client.types import Response

from immich_autotag.logging.levels import LogLevel
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID
from immich_autotag.utils.api_disk_cache import ApiCacheKey, ApiCacheManager

# --- Album API call diagnostics ---
_album_api_call_count = 0
_album_api_ids: set[str] = set()


def print_album_api_call_summary(
    log_func: Optional[Callable[[str, LogLevel], None]] = None,
    loglevel: Optional[LogLevel] = None,
) -> None:
    from immich_autotag.logging.utils import log

    log_fn = log_func or log
    lvl = loglevel or LogLevel.DEBUG
    log_fn(
        f"[DIAG] proxy_get_album_info: total calls={_album_api_call_count}, unique IDs={len(_album_api_ids)}",
        lvl,
    )
    if len(_album_api_ids) < 30:
        log_fn(f"[DIAG] Unique IDs: {_album_api_ids}", lvl)


atexit.register(print_album_api_call_summary)


def proxy_get_album_info(
    *, album_id: AlbumUUID, client: AuthenticatedClient, use_cache: bool = True
) -> AlbumResponseDto | None:
    """
    Centralized wrapper for get_album_info.sync. Includes disk cache.
    """
    global _album_api_call_count
    from immich_autotag.utils.api_disk_cache import ApiCacheKey

    cache_mgr = ApiCacheManager.create(cache_type=ApiCacheKey.ALBUMS)
    # Only accept AlbumUUID
    cache_key = str(album_id)
    cache_data = cache_mgr.load(cache_key)
    if cache_data is not None:
        if isinstance(cache_data, dict):
            return AlbumResponseDto.from_dict(cache_data)
        elif cache_data:
            # Defensive: if cache is a list, return the first
            return AlbumResponseDto.from_dict(cache_data[0])
        else:
            raise RuntimeError(
                f"Invalid cache data for album_id={album_id}: {type(cache_data)}"
            )
    _album_api_call_count += 1
    _album_api_ids.add(cache_key)
    dto = get_album_info.sync(id=album_id.to_uuid(), client=client)
    if dto is not None:
        cache_mgr.save(cache_key, dto.to_dict())
    return dto














