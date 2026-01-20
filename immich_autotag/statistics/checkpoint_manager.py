from pathlib import Path
from typing import TYPE_CHECKING

import attr
from typeguard import typechecked

from immich_autotag.config.manager import ConfigManager
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.statistics._find_max_skip_n_recent import get_max_skip_n_from_recent

if TYPE_CHECKING:
    from .statistics_manager import StatisticsManager


@typechecked
@attr.s(auto_attribs=True, kw_only=True)
class CheckpointManager:
    stats_manager: "StatisticsManager" = attr.ib(
        validator=attr.validators.instance_of(object)
    )
    OVERLAP: int = attr.ib(default=100, init=False)

    @stats_manager.validator
    def _validate_stats_manager(self, attribute, value):
        # Local import to avoid circular dependencies
        from .statistics_manager import StatisticsManager

        if not isinstance(value, StatisticsManager):
            raise TypeError(
                f"stats_manager must be a StatisticsManager, got {type(value)}"
            )

    @typechecked
    def get_effective_skip_n(self) -> int:
        enable_checkpoint_resume = ConfigManager.is_checkpoint_resume_enabled()
        stats_dir = self.stats_manager.stats_dir
        if enable_checkpoint_resume:
            logs_dir = stats_dir.parent if stats_dir else Path("logs")
            max_skip_n = get_max_skip_n_from_recent(
                logs_dir, max_age_hours=3, overlap=self.OVERLAP
            )
            if max_skip_n is not None:
                skip_n = max_skip_n
                log(
                    f"[CHECKPOINT] Will skip {skip_n} assets (from most advanced run in last 3h).",
                    level=LogLevel.PROGRESS,
                )
            else:
                skip_n = 0
                log(
                    "[CHECKPOINT] No previous stats found. Starting from the beginning.",
                    level=LogLevel.PROGRESS,
                )
        else:
            skip_n = 0
            log(
                "[CHECKPOINT] Checkpoint resume is disabled. Starting from the beginning.",
                level=LogLevel.PROGRESS,
            )
        self.stats_manager.set_skip_n(skip_n)
        return skip_n
