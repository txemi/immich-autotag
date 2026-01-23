"""
Utility functions for Immich album API calls (singular album).
"""

import atexit
from uuid import UUID

from immich_client.api.albums import get_album_info
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, log_debug
from immich_autotag.types import ImmichClient

# --- Diagnóstico de llamadas a la API de álbumes ---
_album_api_call_count = 0
_album_api_ids: set[str] = set()


def _print_album_api_call_summary():
    log(
        f"[DIAG] get_album_info_by_id: llamadas totales={_album_api_call_count}, IDs únicos={len(_album_api_ids)}",
        level=LogLevel.DEBUG,
    )
    if len(_album_api_ids) < 30:
        log(f"[DIAG] IDs únicos: {_album_api_ids}", level=LogLevel.DEBUG)


atexit.register(_print_album_api_call_summary)


@typechecked
def get_album_info_by_id(album_id: UUID, client: ImmichClient) -> "AlbumResponseDto":
    """
    Unified wrapper for get_album_info.sync(id=..., client=...).
    Returns the album DTO or raises on error.
    Añade diagnóstico de llamadas totales y IDs únicos.
    """
    global _album_api_call_count
    _album_api_call_count += 1
    _album_api_ids.add(str(album_id))
    a = get_album_info.sync(id=album_id, client=client)
    log_debug(f"Fetched album info for id={album_id}: {a}")
    if a is None:
        raise RuntimeError(f"get_album_info.sync returned None for album id={album_id}")
    return a
