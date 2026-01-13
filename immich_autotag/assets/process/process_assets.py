from __future__ import annotations

import time
from threading import Lock

from typeguard import typechecked

from immich_autotag.assets.process.fetch_total_assets import fetch_total_assets
from immich_autotag.assets.process.log_execution_parameters import (
    log_execution_parameters,
)
from immich_autotag.assets.process.log_final_summary import log_final_summary
from immich_autotag.assets.process.process_assets_sequential import (
    process_assets_sequential,
)
from immich_autotag.assets.process.process_assets_threadpool import (
    process_assets_threadpool,
)
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.config.internal_config import USE_THREADPOOL
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    log_execution_parameters()
    StatisticsManager.get_instance().initialize_for_run(context, max_assets)
    stats = StatisticsManager.get_instance().get_stats()

    if USE_THREADPOOL:
        process_assets_threadpool(context)
        count = None
    else:
        count = process_assets_sequential(context)
    # start_time is now managed by StatisticsManager
    log_final_summary(count if count is not None else 0, stats.started_at)
    StatisticsManager.get_instance().finish_run()
