import uuid
from urllib.parse import ParseResult, urlparse

from typeguard import typechecked

from immich_autotag.config.internal_config import (
    IMMICH_PHOTO_PATH_TEMPLATE,
    IMMICH_WEB_BASE_URL,
)


@typechecked
def get_immich_photo_url(asset_id: uuid.UUID) -> ParseResult:
    """
    Devuelve la URL web de Immich para un asset dado su id (UUID) como ParseResult.
    """
    if not isinstance(asset_id, uuid.UUID):
        raise TypeError(f"asset_id debe ser uuid.UUID, no {type(asset_id)}")
    asset_id_str = str(asset_id)
    url = f"{IMMICH_WEB_BASE_URL}{IMMICH_PHOTO_PATH_TEMPLATE.format(id=asset_id_str)}"
    return urlparse(url)
