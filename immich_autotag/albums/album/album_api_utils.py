"""
Utility functions for Immich album API calls (singular album).
"""

from uuid import UUID

from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.api.immich_proxy.albums import proxy_get_album_info
from immich_autotag.logging.utils import log_trace
from immich_autotag.types import ImmichClient


@typechecked
def get_album_info_by_id(album_id: UUID, client: ImmichClient) -> "AlbumResponseDto":
    """
    Unified wrapper for get_album_info.sync(id=..., client=...).
    Returns the album DTO or raises on error.
    Adds diagnostics for total calls and unique IDs.
    """
    a = proxy_get_album_info(album_id=album_id, client=client)
    # Print only the album id and Immich web link, not the full DTO (avoid long lines)
    from immich_autotag.utils.url_helpers import get_immich_album_url

    album_url = get_immich_album_url(album_id).geturl()
    log_trace(f"Fetched album info for id={album_id}: {album_url}")
    if a is None:
        raise RuntimeError(f"get_album_info.sync returned None for album id={album_id}")
    return a
