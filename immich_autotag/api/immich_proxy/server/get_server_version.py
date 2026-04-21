from typing import Optional

from immich_client.api.server import get_server_version
from immich_client.client import AuthenticatedClient
from immich_client.models.server_version_response_dto import ServerVersionResponseDto


def proxy_get_server_version(
    *, client: AuthenticatedClient
) -> Optional[ServerVersionResponseDto]:
    """Proxy for get_server_version.sync with explicit keyword arguments and type annotations."""
    return get_server_version.sync(client=client)
