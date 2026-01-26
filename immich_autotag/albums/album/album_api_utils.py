"""
Utility functions for Immich album API calls (singular album).
"""

import atexit
from uuid import UUID

from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.api.immich_proxy.albums import proxy_get_album_info
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_trace
from immich_autotag.types import ImmichClient

 # --- Album API call diagnostics ---
_album_api_call_count = 0
_album_api_ids: set[str] = set()


def _print_album_api_call_summary():
    log(
        f"[DIAG] get_album_info_by_id: total calls={_album_api_call_count}, unique IDs={len(_album_api_ids)}",
        level=LogLevel.DEBUG,
    )
    if len(_album_api_ids) < 30:
        log(f"[DIAG] Unique IDs: {_album_api_ids}", level=LogLevel.DEBUG)


atexit.register(_print_album_api_call_summary)


@typechecked
def get_album_info_by_id(album_id: UUID, client: ImmichClient) -> "AlbumResponseDto":
    """
    Unified wrapper for get_album_info.sync(id=..., client=...).
    Returns the album DTO or raises on error.
    Adds diagnostics for total calls and unique IDs.
    """
    global _album_api_call_count
    _album_api_call_count += 1
    _album_api_ids.add(str(album_id))
    a = proxy_get_album_info(album_id=album_id, client=client)
    # Print only the album id and Immich web link, not the full DTO (avoid long lines)
    from immich_autotag.utils.url_helpers import get_immich_album_url

    album_url = get_immich_album_url(album_id).geturl()
    log_trace(f"Fetched album info for id={album_id}: {album_url}")
    if a is None:
        raise RuntimeError(f"get_album_info.sync returned None for album id={album_id}")
    return a
