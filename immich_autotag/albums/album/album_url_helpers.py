from uuid import UUID

from immich_client.models.album_response_dto import AlbumResponseDto

from immich_autotag.types.uuid_wrappers import AlbumUUID
from immich_autotag.utils.url_helpers import get_immich_album_url


def album_url_from_dto(dto: AlbumResponseDto) -> str:
    """
    Given an AlbumResponseDto, returns the Immich album URL as a string (or None if not possible).
    """
    try:
        album_id = AlbumUUID.from_uuid(UUID(dto.id))
        return get_immich_album_url(album_id).geturl()
    except Exception:
        return "<invalid>"
