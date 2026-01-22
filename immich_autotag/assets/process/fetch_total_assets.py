from __future__ import annotations

from immich_client.api.server import get_server_statistics
from typeguard import typechecked

from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def fetch_total_assets(context: ImmichContext) -> int :
    stats = get_server_statistics.sync(client=context.client)
    total_assets = stats.photos + stats.videos
    log(
        f"Total assets (photos + videos) reported by Immich: {total_assets}",
        level=LogLevel.PROGRESS,
    )
    return total_assets