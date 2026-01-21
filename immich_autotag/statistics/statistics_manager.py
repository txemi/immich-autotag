from typing import TYPE_CHECKING

import git  # GitPython

from immich_autotag.context.immich_context import ImmichContext

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper

"""
statistics_manager.py

Core statistics management logic for tracking progress, statistics, and historical runs.
Handles YAML serialization, extensibility, and replaces legacy checkpoint logic.
"""


from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.tags.modification_kind import ModificationKind

from threading import RLock

import attr

from immich_autotag.statistics.constants import RUN_STATISTICS_FILENAME
from immich_autotag.utils.perf.performance_tracker import PerformanceTracker
from immich_autotag.utils.run_output_dir import get_run_output_dir

from .checkpoint_manager import CheckpointManager
from .run_statistics import RunStatistics
from .tag_stats_manager import TagStatsManager

# Module singleton
_instance = None


@attr.s(auto_attribs=True, kw_only=True)
class StatisticsManager:

    _perf_tracker: PerformanceTracker = attr.ib(default=None, init=False, repr=False)
    stats_dir: Path = attr.ib(factory=get_run_output_dir, init=False, repr=False)
    _instance: "StatisticsManager" = attr.ib(default=None, init=False, repr=False)
    _lock: RLock = attr.ib(factory=RLock, init=False, repr=False)
    _current_stats: Optional[RunStatistics] = attr.ib(
        default=None, init=False, repr=False
    )
    _current_file: Optional[Path] = attr.ib(default=None, init=False, repr=False)

    # Event counters are now stored in self._current_stats.event_counters
    def __attrs_post_init__(self) -> None:
        # The folder is already created by get_run_output_dir
        global _instance
        if _instance is not None and _instance is not self:
            raise RuntimeError(
                "StatisticsManager instance already exists. Use StatisticsManager.get_instance() instead of creating a new one."
            )
        _instance = self
        self.checkpoint = CheckpointManager(stats_manager=self)
        self.tags = TagStatsManager(stats_manager=self)
        self.checkpoint = CheckpointManager(stats_manager=self)

    @typechecked
    def increment_event(
        self, event_kind: "ModificationKind", extra_key: "TagWrapper | None" = None
    ) -> None:
        """
        Increment the counter for the given event kind (ModificationKind).
        If extra_key (TagWrapper) is provided, it is concatenated to the event_kind name for per-key statistics.
        """
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.increment_event(event_kind, extra_key=extra_key)

    @typechecked
    def get_progress_description(self) -> str:
        from immich_autotag.utils.perf.progress_description import (
            get_progress_description_from_perf_tracker,
        )

        count = self._current_stats.count if self._current_stats else 0
        return get_progress_description_from_perf_tracker(
            self._perf_tracker, current_count=count
        )

    @typechecked
    def _try_init_perf_tracker(self):
        if self._perf_tracker is not None:
            return
        total = self._current_stats.total_assets or self._current_stats.max_assets
        if total is not None:
            import time

            from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
            from immich_autotag.utils.perf.time_estimation_mode import (
                TimeEstimationMode,
            )

            self._perf_tracker = PerformanceTracker(
                start_time=time.time(),
                log_interval=5,
                estimator=AdaptiveTimeEstimator(),
                estimation_mode=TimeEstimationMode.LINEAR,
                total_to_process=total,
                total_assets=self._current_stats.total_assets,
                skip_n=self._current_stats.skip_n,
            )

    @typechecked
    def set_total_assets(self, total_assets: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.total_assets = total_assets
            self._save_to_file()
            self._try_init_perf_tracker()

    @typechecked
    def set_max_assets(self, max_assets: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.max_assets = max_assets
            self._save_to_file()
            self._try_init_perf_tracker()

    def maybe_print_progress(self, count: int) -> None:
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. Call set_total_assets or set_max_assets before processing."
            )
        self._perf_tracker.update(count)

    @typechecked
    def print_progress(self, count: int) -> None:
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. Call set_total_assets or set_max_assets before processing."
            )
        self._perf_tracker.print_progress(count)

    @staticmethod
    def get_instance() -> "StatisticsManager":
        global _instance
        if _instance is None:
            StatisticsManager()
        return _instance

    @typechecked
    def start_run(self, initial_stats: Optional[RunStatistics] = None) -> None:
        with self._lock:
            if self._current_stats is not None:
                return
            # Get git version using GitPython
            try:
                repo = git.Repo(search_parent_directories=True)
                git_describe_runtime = repo.git.describe(
                    "--tags", "--always", "--dirty"
                )
            except Exception:
                git_describe_runtime = None
            # Get git describe string from version.py
            try:
                from immich_autotag.version import __git_describe__

                git_describe_package = __git_describe__
            except Exception:
                git_describe_package = None
            self._current_stats = initial_stats or RunStatistics(
                last_processed_id=None,
                count=0,
                git_describe_runtime=git_describe_runtime,
                git_describe_package=git_describe_package,
            )
            self._current_file = self.stats_dir / RUN_STATISTICS_FILENAME
            self._save_to_file()

    def _save_to_file(self) -> None:
        if self._current_stats and self._current_file:
            # Always update progress_description before saving
            self._current_stats.progress_description = self.get_progress_description()
            with open(self._current_file, "w", encoding="utf-8") as f:
                f.write(self._current_stats.to_yaml())

    @typechecked
    def get_stats(self) -> RunStatistics:
        if self._current_stats is None:
            self.start_run()
        return self._current_stats

    @typechecked
    def update_checkpoint(self, last_processed_id: str, count: int) -> RunStatistics:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.last_processed_id = last_processed_id
            self._current_stats.count = count
            # Only save to disk every 100 assets (not every asset) for performance
            if count % 100 == 0:
                self._save_to_file()
        self.maybe_print_progress(count)
        return self._current_stats

    @typechecked
    def save(self) -> None:
        with self._lock:
            self._save_to_file()

    @typechecked
    def delete_all(self) -> None:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            "StatisticsManager.delete_all() is deprecated and should not be used. Statistics are preserved for logging.",
            level=LogLevel.WARNING,
        )

    @typechecked
    def finish_run(self) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            from datetime import datetime, timezone

            self._current_stats.finished_at = datetime.now(timezone.utc)
            self._save_to_file()

    @property
    def RELEVANT_TAGS(self):
        from immich_autotag.config.manager import (
            ConfigManager,
        )

        manager = ConfigManager.get_instance()
        config = manager.config
        try:
            return {
                config.classification.autotag_unknown,
                config.classification.autotag_conflict,
                config.duplicate_processing.autotag_album_conflict,
                config.duplicate_processing.autotag_classification_conflict,
            }
        except AttributeError as e:
            raise RuntimeError(f"Missing expected autotag category in config: {e}")

    @typechecked
    def process_asset_tags(self, tag_names: list[str]) -> None:
        self.tags.process_asset_tags(tag_names)

    @typechecked
    def increment_tag_added(self, tag: "TagWrapper") -> None:
        self.tags.increment_tag_added(tag)

    @typechecked
    def increment_tag_removed(self, tag: "TagWrapper") -> None:
        self.tags.increment_tag_removed(tag)

    @typechecked
    def set_skip_n(self, skip_n: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.skip_n = skip_n
            self._save_to_file()

    @typechecked
    def get_effective_skip_n(self) -> int:
        return self.checkpoint.get_effective_skip_n()

    @typechecked
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None",
    ) -> None:
        self.tags.increment_tag_action(tag, kind, album)

    # Tag/album methods delegated to TagStatsManager
    @typechecked
    def initialize_for_run(
        self, context: "ImmichContext", max_assets: int | None
    ) -> None:
        from immich_autotag.assets.process.fetch_total_assets import fetch_total_assets

        total_assets = fetch_total_assets(context)
        skip_n = self.get_effective_skip_n()
        self.set_max_assets(max_assets if max_assets is not None else -1)
        self.set_skip_n(skip_n)
        self._current_stats.total_assets = total_assets
