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
from immich_autotag.assets.process.register_execution_parameters import (
    register_execution_parameters,
)
from immich_autotag.assets.process.resolve_checkpoint import resolve_checkpoint
from immich_autotag.config.internal_config import USE_THREADPOOL
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.statistics.statistics_manager import StatisticsManager
from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator


@typechecked
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    estimator = AdaptiveTimeEstimator(alpha=0.05)
    tag_mod_report = ModificationReport.get_instance()
    lock = Lock()
    LOG_INTERVAL = 5  # seconds
    start_time = time.time()

    log_execution_parameters()
    total_assets = fetch_total_assets(context)
    last_processed_id, skip_n = resolve_checkpoint()
    register_execution_parameters(total_assets, max_assets, skip_n)
    total_to_process = None
    if total_assets is not None:
        total_to_process = total_assets
        if skip_n:
            total_to_process = max(1, total_assets - skip_n)

    if USE_THREADPOOL:
        process_assets_threadpool(
            context,
            max_assets,
            tag_mod_report,
            lock,
            estimator,
            total_to_process,
            skip_n,
            total_assets,
            LOG_INTERVAL,
            start_time,
        )
        # No checkpoint update in threadpool mode, so count is not tracked here
        count = None
    else:
        count = process_assets_sequential(
            context,
            max_assets,
            skip_n,
            last_processed_id,
            tag_mod_report,
            lock,
            estimator,
            total_to_process,
            LOG_INTERVAL,
            start_time,
            total_assets,
        )
    log_final_summary(count if count is not None else 0, tag_mod_report, start_time)
    # Mark statistics completion
    StatisticsManager.get_instance().finish_run()
