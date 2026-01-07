from __future__ import annotations

from typeguard import typechecked

from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def register_execution_parameters(
    total_assets: int | None, max_assets: int | None, skip_n: int
) -> None:
    StatisticsManager.get_instance().set_max_assets(
        max_assets if max_assets is not None else -1
    )
    StatisticsManager.get_instance().set_skip_n(skip_n)
