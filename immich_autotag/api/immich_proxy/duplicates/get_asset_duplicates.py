from typing import Optional

from immich_client.api.duplicates import get_asset_duplicates
from immich_client.client import AuthenticatedClient

__all__ = ["proxy_get_asset_duplicates"]
from immich_client.models.duplicate_response_dto import DuplicateResponseDto


def proxy_get_asset_duplicates(
    *, client: AuthenticatedClient
) -> Optional[list[DuplicateResponseDto]]:
    return get_asset_duplicates.sync(client=client)
