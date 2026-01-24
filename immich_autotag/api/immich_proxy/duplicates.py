
from immich_client.api.duplicates import get_asset_duplicates
from immich_client.client import AuthenticatedClient


def proxy_get_asset_duplicates(
    *, client: AuthenticatedClient
) -> list[DuplicateResponseDto]:
    return get_asset_duplicates.sync(client=client)
