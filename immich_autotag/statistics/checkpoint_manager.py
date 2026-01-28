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
@attr.s(auto_attribs=True, kw_only=True, slots=True)
class CheckpointManager:
    stats_manager: "StatisticsManager" = attr.ib(init=True)
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
    def get_effective_skip_n(
        self, config_skip_n: int = 0, config_resume_previous: bool = True
    ) -> int:
        """
        Decides the value of skip_n and makes its origin clear in the log: previous checkpoint, config, or none.
        """
        enable_checkpoint_resume = ConfigManager.is_checkpoint_resume_enabled()
        from immich_autotag.run_output.manager import RunOutputManager

        run_execution = RunOutputManager.get_run_output_dir()
        stats_dir = run_execution.get_run_statistics_path()
        skip_n = 0
        origen = None
        if enable_checkpoint_resume and config_resume_previous:
            logs_dir = stats_dir.parent if stats_dir else Path("logs")
            max_skip_n = get_max_skip_n_from_recent(
                logs_dir, max_age_hours=3, overlap=self.OVERLAP
            )
            if max_skip_n is not None and max_skip_n > 0:
                skip_n = max_skip_n
                origen = f"checkpoint (previous stats in logs, overlap={self.OVERLAP})"
            elif config_skip_n > 0:
                skip_n = config_skip_n
                origen = "configuration (skip.skip_n)"
            else:
                skip_n = 0
                origen = "none (starting from the beginning)"
        elif config_skip_n > 0:
            skip_n = config_skip_n
            origen = "configuration (skip.skip_n)"
        else:
            skip_n = 0
            if not enable_checkpoint_resume:
                origen = "checkpoint disabled"
            else:
                origen = "none (starting from the beginning)"

        log(
            f"[CHECKPOINT] skip_n={skip_n} (origen: {origen})",
            level=LogLevel.PROGRESS,
        )
        return skip_n
