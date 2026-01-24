from immich_client import Client
from immich_client.api.server import get_server_statistics
from immich_client.models.server_stats_response_dto import ServerStatsResponseDto


def proxy_get_server_statistics(*, client: Client) -> ServerStatsResponseDto:
    """Proxy for get_server_statistics.sync with explicit keyword arguments and type annotations."""
    return get_server_statistics.sync(client=client)
