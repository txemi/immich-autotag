"""
Utility functions for Immich album API calls (singular album).
"""

from uuid import UUID

from immich_client.api.albums import get_album_info
from immich_client.models.album_response_dto import AlbumResponseDto
from typeguard import typechecked

from immich_autotag.types import ImmichClient


@typechecked
def get_album_info_by_id(album_id: UUID, client: ImmichClient) -> AlbumResponseDto:
    """
    Unified wrapper for get_album_info.sync(id=..., client=...).
    Returns the album DTO or raises on error.
    """
    uuid_str = str(album_id)
    return get_album_info.sync(id=uuid_str, client=client)
