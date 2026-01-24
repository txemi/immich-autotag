from immich_client.api.duplicates import get_asset_duplicates
from immich_client.client import AuthenticatedClient
from immich_client.models.duplicate_response_dto import DuplicateResponseDto


def proxy_get_asset_duplicates(
    *, client: AuthenticatedClient
) -> list[DuplicateResponseDto]:
    return get_asset_duplicates.sync(client=client)
