from datetime import datetime
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

        skip_n = 0
        origen = None
        if enable_checkpoint_resume and config_resume_previous:
            max_skip_n = get_max_skip_n_from_recent(
                max_age_hours=72, overlap=self.OVERLAP
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

    @typechecked
    def maybe_archive_completed_cycle(self, total_assets: int) -> bool:
        """
        Detect whether the previous pass already covered the whole library
        and, if so, archive its run dirs out of `logs_local/` so the next
        skip_n calculation falls back to config (typically 0) and a fresh
        cycle starts.

        Without this, the max-recent-count logic in
        `get_max_skip_n_from_recent` keeps resuming near the library end
        forever once a pass has reached the final assets — every new build
        sees the high count YAML and resumes one overlap before it.

        Detection: any recent run YAML with count >= total_assets - OVERLAP
        is considered an end-of-cycle marker.

        Side effect: when triggered, all current recent run dirs are moved
        to `<logs_local>/_archive/cycle-<YYYYmmdd_HHMMSS>/`. Callers should
        recompute skip_n after this returns True (the existing
        `StatisticsManager._set_skip_n` does the right thing once the
        directory is empty of recent dirs).

        Returns True if archiving happened, False otherwise.
        """
        from immich_autotag.run_output.manager import RunOutputManager
        from immich_autotag.statistics.run_statistics import RunStatistics

        threshold = total_assets - self.OVERLAP
        recent_dirs = list(
            RunOutputManager.current().find_recent_run_dirs(max_age_hours=72)
        )

        cycle_completed = False
        for run_exec in recent_dirs:
            stats_path = run_exec.get_run_statistics_path()
            if not stats_path.exists():
                continue
            try:
                stats = RunStatistics.from_yaml(stats_path)
                if stats.count >= threshold:
                    cycle_completed = True
                    break
            except Exception as e:
                log(
                    f"[CHECKPOINT] Could not read {stats_path} during cycle "
                    f"detection: {e}",
                    level=LogLevel.WARNING,
                )
                continue

        if not cycle_completed:
            return False

        if not recent_dirs:
            # Should not happen given cycle_completed=True implies at least one
            # readable YAML, but be defensive.
            return False

        # Use the parent of any recent run dir as the logs_local root
        logs_dir = recent_dirs[0].path.parent
        archive_root = logs_dir / "_archive" / f"cycle-{datetime.now():%Y%m%d_%H%M%S}"
        archive_root.mkdir(parents=True, exist_ok=True)

        archived = 0
        for run_exec in recent_dirs:
            try:
                run_exec.path.rename(archive_root / run_exec.path.name)
                archived += 1
            except Exception as e:
                log(
                    f"[CHECKPOINT] Failed to archive {run_exec.path}: {e}",
                    level=LogLevel.WARNING,
                )

        log(
            f"[CHECKPOINT] End of cycle detected: a recent run reached "
            f"count >= {threshold} (= total_assets {total_assets} - "
            f"OVERLAP {self.OVERLAP}). Archived {archived} run dir(s) to "
            f"{archive_root}. Next skip_n will fall back to config "
            f"(typically 0), starting a fresh pass.",
            level=LogLevel.PROGRESS,
        )
        return True
