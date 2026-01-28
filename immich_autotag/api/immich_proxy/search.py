from typing import Any

from immich_client.api.search import search_assets
from immich_client.client import AuthenticatedClient
from immich_client.models.metadata_search_dto import MetadataSearchDto
from immich_client.models.search_response_dto import SearchResponseDto
from immich_client.types import Response


def proxy_search_assets(
    *, client: AuthenticatedClient, body: MetadataSearchDto
) -> Response[SearchResponseDto]:
    return search_assets.sync_detailed(client=client, body=body)
