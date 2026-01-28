
from typing import List
import atexit
from uuid import UUID
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

from immich_autotag.utils.api_disk_cache import (
    get_entity_from_cache,
    save_entity_to_cache,
)
from immich_autotag.logging.levels import LogLevel

# --- Album API call diagnostics ---
_album_api_call_count = 0
_album_api_ids: set[str] = set()


from typing import Callable, Optional

def print_album_api_call_summary(
    log_func: Optional[Callable[[str, LogLevel], None]] = None,
    loglevel: Optional[LogLevel] = None,
) -> None:
    from immich_autotag.logging.levels import LogLevel
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
    *, album_id: UUID, client: AuthenticatedClient, use_cache: bool = True
) -> AlbumResponseDto | None:
    """
    Centralized wrapper for get_album_info.sync. Includes disk cache.
    """
    global _album_api_call_count, _album_api_ids
    from immich_autotag.utils.api_disk_cache import ApiCacheKey

    cache_data = get_entity_from_cache(
        entity=ApiCacheKey.ALBUMS, key=str(album_id), use_cache=use_cache
    )
    if cache_data is not None:
        return AlbumResponseDto.from_dict(cache_data)
    _album_api_call_count += 1
    _album_api_ids.add(str(album_id))
    dto = get_album_info.sync(id=album_id, client=client)
    if dto is not None:
        from immich_autotag.utils.api_disk_cache import ApiCacheKey

        save_entity_to_cache(
            entity=ApiCacheKey.ALBUMS, key=str(album_id), data=dto.to_dict()
        )


def proxy_remove_asset_from_album(
    *, album_id: UUID, client: AuthenticatedClient, asset_ids: List[UUID]
) -> list[BulkIdResponseDto]:
    return remove_asset_from_album.sync(
        id=album_id, client=client, body=BulkIdsDto(ids=asset_ids)
    )


def proxy_update_album_info(
    *, album_id: UUID, client: AuthenticatedClient, body: UpdateAlbumDto
) -> AlbumResponseDto:
    result = update_album_info.sync(id=album_id, client=client, body=body)
    if result is None:
        raise RuntimeError("Failed to update album info")
    return result


def proxy_add_users_to_album(
    *, album_id: UUID, client: AuthenticatedClient, body: AddUsersDto
) -> AlbumResponseDto:
    from immich_client.api.albums import add_users_to_album

    result = add_users_to_album.sync(id=album_id, client=client, body=body)
    if result is None:
        raise RuntimeError("Failed to add users to album")
    return result


def proxy_get_all_albums(*, client: AuthenticatedClient) -> list[AlbumResponseDto]:
    result = get_all_albums.sync(client=client)
    if result is None:
        raise RuntimeError("Failed to fetch albums: API returned None")
    return result


def proxy_add_assets_to_album(
    *, album_id: UUID, client: AuthenticatedClient, asset_ids: List[UUID]
) -> list[BulkIdResponseDto]:
    result = add_assets_to_album.sync(
        id=album_id, client=client, body=BulkIdsDto(ids=asset_ids)
    )
    if result is None:
        raise RuntimeError(
            f"Failed to add assets to album {album_id}: API returned None"
        )
    return result
