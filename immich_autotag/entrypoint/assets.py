from __future__ import annotations

from immich_autotag.assets.process.process_assets import process_assets
from immich_autotag.config.filter_wrapper import FilterConfigWrapper
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext


def process_assets_or_filtered(manager: ConfigManager, context: ImmichContext) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.perf.perf_phase_tracker import perf_phase_tracker


    filter_wrapper = FilterConfigWrapper.from_filter_config(manager.get_config_or_raise().filters)

    if filter_wrapper.is_focused():
        ruleset = filter_wrapper.get_filter_in_ruleset()
        assets_to_process = ruleset.get_filtered_in_assets_by_uuid(context)
        from immich_autotag.assets.process.process_single_asset import (
            process_single_asset,
        )

        for wrapper in assets_to_process:
            process_single_asset(asset_wrapper=wrapper)
    else:
        import time

        perf_phase_tracker.mark(phase="assets", event="start")
        log(
            "[PROGRESS] [ASSET-PROCESS] Starting asset processing",
            level=LogLevel.PROGRESS,
        )
        t0 = time.time()
        process_assets(context)
        t1 = time.time()
        log(
            f"[PROGRESS] [ASSET-PROCESS] Finished asset processing. Elapsed: {t1-t0:.2f} seconds.",
            level=LogLevel.PROGRESS,
        )
        perf_phase_tracker.mark(phase="assets", event="end")
