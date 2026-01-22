from typing import TYPE_CHECKING

import git  # GitPython

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
    from immich_autotag.report.modification_kind import ModificationKind


import time
from threading import RLock

import attr

from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

from .checkpoint_manager import CheckpointManager
from .run_statistics import RunStatistics
from .tag_stats_manager import TagStatsManager

# Module singleton
_instance = None


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class StatisticsManager:
    _perf_tracker: PerformanceTracker = attr.ib(default=None, init=False, repr=False)
    _lock: RLock = attr.ib(factory=RLock, init=False, repr=False)
    _current_stats: Optional[RunStatistics] = attr.ib(
        default=None, init=False, repr=False
    )
    _current_file: Optional[Path] = attr.ib(default=None, init=False, repr=False)
    _checkpoint: CheckpointManager = attr.ib(default=None, init=False, repr=False)
    _tags: TagStatsManager = attr.ib(default=None, init=False, repr=False)

    # Event counters are now stored in self._current_stats.event_counters
    def __attrs_post_init__(self) -> None:
        # The folder is already created by get_run_output_dir
        global _instance
        if _instance is not None and _instance is not self:
            raise RuntimeError(
                "StatisticsManager instance already exists. Use StatisticsManager.get_instance() instead of creating a new one."
            )
        _instance = self
        # Initialize declared attributes
        self._checkpoint = CheckpointManager(stats_manager=self)
        self._tags = TagStatsManager(stats_manager=self)

    @typechecked
    def get_checkpoint_manager(self) -> CheckpointManager:
        return self._checkpoint

    @typechecked
    def increment_event(
        self, event_kind: "ModificationKind", extra_key: "TagWrapper | None" = None
    ) -> None:
        """
        Increment the counter for the given event kind (ModificationKind).
        If extra_key (TagWrapper) is provided, it is concatenated to the event_kind name for per-key statistics.
        """
        with self._lock:

            self.start_run().increment_event(event_kind, extra_key=extra_key)

    @typechecked
    def get_progress_description(self) -> str:
        count = self.start_run().count
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. Call set_total_assets or set_max_assets before processing."
            )
        return self._get_or_create_perf_tracker().get_progress_description(count)

    @typechecked
    def _get_or_create_perf_tracker(self):
        if self._perf_tracker is not None:
            return self._perf_tracker
        total_assets = self.start_run().total_assets
        max_assets = self.start_run().max_assets

        from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
        from immich_autotag.utils.perf.time_estimation_mode import (
            TimeEstimationMode,
        )

        self._perf_tracker = PerformanceTracker(
            start_time=time.time(),
            log_interval=5,
            estimator=AdaptiveTimeEstimator(),
            estimation_mode=TimeEstimationMode.LINEAR,
            total_assets=total_assets,
            max_assets=max_assets,
            skip_n=self.start_run().skip_n,
        )
        return self._perf_tracker

    @typechecked
    def set_total_assets(self, total_assets: int) -> None:
        with self._lock:
            self.start_run().total_assets = total_assets
            self._save_to_file()
            self._get_or_create_perf_tracker()

    @typechecked
    def set_max_assets(self, max_assets: int) -> None:
        with self._lock:
            self.start_run().max_assets = max_assets
            self._save_to_file()
            self._get_or_create_perf_tracker()

    def maybe_print_progress(self, count: int) -> None:
        self._get_or_create_perf_tracker().update(count)

    @typechecked
    def print_progress(self, count: int) -> None:
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. Call set_total_assets or set_max_assets before processing."
            )
        self._get_or_create_perf_tracker().print_progress(count)

    @staticmethod
    def get_instance() -> "StatisticsManager":
        global _instance
        if _instance is None:
            StatisticsManager()
        return _instance

    @typechecked
    def start_run(self, initial_stats: Optional[RunStatistics] = None) -> RunStatistics:
        # TODO: refactorizar a get_s
        with self._lock:
            if self._current_stats is not None:
                return self._current_stats
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
            self._current_stats.save_to_file()
            return self._current_stats

    def _save_to_file(self) -> None:
        if self._current_stats and self._current_file:
            # Always update progress_description before saving
            self.start_run().progress_description = self.get_progress_description()
            self.start_run().save_to_file()

    @typechecked
    def get_stats(self) -> RunStatistics:

        return self.start_run()

    @typechecked
    def update_checkpoint(self, last_processed_id: str, count: int) -> RunStatistics:
        with self._lock:

            self.start_run().last_processed_id = last_processed_id
            self.start_run().count = count
            # Only save to disk every 100 assets (not every asset) for performance
            if count % 100 == 0:
                self._save_to_file()
        self.maybe_print_progress(count)
        return self.start_run()

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
        from datetime import datetime, timezone

        with self._lock:
            now = datetime.now(timezone.utc)
            self.start_run().finished_at = now
            # Sumar el tiempo de esta sesión al acumulado
            if self.start_run().started_at is not None:
                session_time = (now - self._current_stats.started_at).total_seconds()
                self.start_run().previous_sessions_time += session_time
            self._save_to_file()

    @typechecked
    def abrupt_exit(self) -> None:
        from datetime import datetime, timezone

        with self._lock:
            now = datetime.now(timezone.utc)
            self.start_run().abrupt_exit_at = now
            # Sumar el tiempo de esta sesión al acumulado
            if self.start_run().started_at is not None:
                session_time = (now - self._current_stats.started_at).total_seconds()
                self.start_run().previous_sessions_time += session_time
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
        self._tags.process_asset_tags(tag_names)

    @typechecked
    def increment_tag_added(self, tag: "TagWrapper") -> None:
        self._tags.increment_tag_added(tag)

    @typechecked
    def increment_tag_removed(self, tag: "TagWrapper") -> None:
        self._tags.increment_tag_removed(tag)

    @typechecked
    def set_skip_n(self, skip_n: int) -> None:
        with self._lock:

            self.start_run().skip_n = skip_n
            self._save_to_file()

    @typechecked
    def get_effective_skip_n(self) -> int:
        return self._checkpoint.get_effective_skip_n()

    @typechecked
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None",
    ) -> None:
        self._tags.increment_tag_action(tag, kind, album)

    # Tag/album methods delegated to TagStatsManager
    @typechecked
    def initialize_for_run(self, max_assets: int) -> None:
        total_assets = max_assets
        self._get_or_create_perf_tracker().total_assets = total_assets
        # Inicializar primero total_assets para que el PerformanceTracker pueda inicializarse correctamente
        self._current_stats.total_assets = total_assets
        self.set_max_assets(max_assets if max_assets is not None else -1)
        skip_n = self.get_effective_skip_n()
        self.set_skip_n(skip_n)
