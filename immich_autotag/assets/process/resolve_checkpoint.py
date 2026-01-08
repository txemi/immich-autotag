from __future__ import annotations

from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.statistics.statistics_manager import StatisticsManager


@typechecked
def resolve_checkpoint() -> tuple[str | None, int]:
    return StatisticsManager.get_instance().get_effective_skip_n()
