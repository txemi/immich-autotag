import uuid
from immich_autotag.config.internal_config import IMMICH_WEB_BASE_URL
from typeguard import typechecked


@typechecked
def get_immich_album_url(album_id: uuid.UUID | str) -> str:
    """
    Returns the Immich web URL for an album given its id (UUID or str).
    """
    if not isinstance(album_id, (uuid.UUID, str)):
        raise TypeError(f"album_id must be uuid.UUID or str, not {type(album_id)}")
    album_id_str = str(album_id)
    return f"{IMMICH_WEB_BASE_URL}/albums/{album_id_str}"
