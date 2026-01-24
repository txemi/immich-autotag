from __future__ import annotations

from immich_client.api.server import get_server_statistics
from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.types import ImmichClient


@typechecked
def fetch_total_assets(client: ImmichClient) -> int:
    stats = get_server_statistics.sync(client=client)
    if stats is None:
        raise RuntimeError("Failed to fetch server statistics: API returned None")
    total_assets = stats.photos + stats.videos
    log(
        f"Total assets (photos + videos) reported by Immich: {total_assets}",
        level=LogLevel.PROGRESS,
    )
    return total_assets
