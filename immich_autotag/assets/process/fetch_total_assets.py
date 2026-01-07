from __future__ import annotations

from immich_client.api.server import get_server_statistics
from typeguard import typechecked

from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def fetch_total_assets(context: ImmichContext) -> int | None:
    try:
        stats = get_server_statistics.sync(client=context.client)
        total_assets = stats.photos + stats.videos
        log(
            f"Total assets (photos + videos) reported by Immich: {total_assets}",
            level=LogLevel.PROGRESS,
        )
        StatisticsManager.get_instance().set_total_assets(total_assets)
        return total_assets
    except Exception as e:
        log(
            f"[ERROR] Could not get total assets from API: {e}",
            level=LogLevel.IMPORTANT,
        )
        return None
