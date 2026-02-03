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








def proxy_get_all_albums(*, client: AuthenticatedClient) -> list[AlbumResponseDto]:
    result = get_all_albums.sync(client=client)
    if result is None:
        raise RuntimeError("Failed to fetch albums: API returned None")
    return result


def proxy_get_album_page(
    *, client: AuthenticatedClient, page: int, page_size: int = 100
) -> list[AlbumResponseDto]:
    """
    Fetch a page of albums, using disk cache for each page.
    """

    cache_mgr = ApiCacheManager.create(cache_type=ApiCacheKey.ALBUM_PAGES)
    cache_key = f"page_{page}_size_{page_size}"
    cache_data = cache_mgr.load(cache_key)
    if cache_data is not None:
        # Defensive: filter only dicts
        return [
            AlbumResponseDto.from_dict(dto)
            for dto in cache_data
            if isinstance(dto, dict)
        ]
    # If not cached, fetch all albums and simulate pagination
    from immich_client.api.albums import get_all_albums

    all_albums = get_all_albums.sync(client=client)
    if all_albums is None:
        raise RuntimeError("Failed to fetch albums: API returned None")
    # Simulate pagination
    start = (page - 1) * page_size
    end = start + page_size
    page_albums = all_albums[start:end]
    # Save to cache
    cache_mgr.save(cache_key, [dto.to_dict() for dto in page_albums])
    return page_albums


def proxy_add_assets_to_album(
    *, album_id: AlbumUUID, client: AuthenticatedClient, asset_ids: list[AssetUUID]
) -> list[BulkIdResponseDto]:
    # Convert AssetUUIDs to UUIDs for API compatibility
    uuid_ids = [a.to_uuid() for a in asset_ids]
    result = add_assets_to_album.sync(
        id=album_id.to_uuid(), client=client, body=BulkIdsDto(ids=uuid_ids)
    )
    if result is None:
        raise RuntimeError(
            f"Failed to add assets to album {album_id}: API returned None"
        )
    return result


def proxy_delete_album(
    album_id: "AlbumUUID", client: "AuthenticatedClient"
) -> Response[Any]:
    """
    Deletes an album by UUID using the ImmichClient API.
    Raises an exception if the operation fails.

        NOTE: This function intentionally returns the Response[Any] object from the Immich client.
        Do NOT change the return type to None. The contract is:
            - If the operation fails, an exception is raised.
            - If the operation succeeds, the response object is returned for advanced inspection.
        This is required by design and for full control of the flow in higher layers.
        If any linting, formatting, or refactoring tool suggests removing the return,
        IGNORE IT and keep this contract. Documented by explicit user request.
    """
    from immich_client.api.albums.delete_album import (
        sync_detailed as delete_album_sync_detailed,
    )

    response = delete_album_sync_detailed(id=album_id.to_uuid(), client=client)
    if response.status_code != 204:
        raise RuntimeError(
            f"Failed to delete album {album_id}: status {response.status_code}, content: {response.content!r}"
        )
    return response
