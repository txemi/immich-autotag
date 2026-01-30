"""
statistics_manager.py

Core statistics management logic for tracking progress, statistics, and historical runs.
Handles YAML serialization, extensibility, and replaces legacy checkpoint logic.
"""

import time
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Optional

import attr
import git
from typeguard import typechecked

from immich_autotag.types.uuid_wrappers import AssetUUID
from immich_autotag.config.models import UserConfig  # GitPython
from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

from .checkpoint_manager import CheckpointManager
from .run_statistics import RunStatistics
from .tag_stats_manager import TagStatsManager

if TYPE_CHECKING:
    from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

# Module singleton
_instance = None


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class StatisticsManager:

    #
    # IMPORTANT NOTE ABOUT attrs AND THE LINTER:
    #
    # By convention, the constructor arguments for classes using attrs should be public (no leading underscore),
    # even if the internal attributes are private (with leading underscore). attrs requires this to function correctly.
    # If the linter (e.g., flake8, pylint, mypy) complains about the mismatch between public arguments and private attributes,
    # silence the warning with a noqa or specific configuration, as this is the correct pattern with attrs.
    # Example: pylint: disable=attribute-defined-outside-init
    #
    # Reference: https://www.attrs.org/en/stable/init.html#private-attributes
    _perf_tracker: PerformanceTracker = attr.ib(
        default=None, init=False, repr=False
    )  # noqa
    _lock: RLock = attr.ib(factory=RLock, init=False, repr=False)  # noqa
    _current_stats: Optional[RunStatistics] = attr.ib(
        default=None, init=False, repr=False
    )  # noqa
    _current_file: Optional[Path] = attr.ib(
        default=None, init=False, repr=False
    )  # noqa
    _checkpoint: CheckpointManager = attr.ib(
        default=None, init=False, repr=False
    )  # noqa
    _tags: TagStatsManager = attr.ib(default=None, init=False, repr=False)  # noqa

    @typechecked
    def _get_or_create_perf_tracker(self) -> PerformanceTracker:
        if self._perf_tracker is not None:
            return self._perf_tracker
        total_assets = self.get_or_create_run_stats().total_assets
        max_assets = self.get_or_create_run_stats().max_assets

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
            skip_n=self.get_or_create_run_stats().skip_n,
        )
        return self._perf_tracker

    def _save_to_file(self) -> None:
        if self._current_stats and self._current_file:
            # Always update progress_description before saving
            self.get_or_create_run_stats().progress_description = (
                self.get_progress_description()
            )
            self.get_or_create_run_stats().save_to_file()

    @typechecked
    def _set_max_assets(self) -> None:
        """
        Reads max_assets from the configuration and updates the value in statistics
        and the PerformanceTracker.
        """
        from immich_autotag.config.manager import ConfigManager

        config = ConfigManager.get_instance().get_config()
        assert isinstance(config, UserConfig)
        # Direct access, if any attribute is missing, let it fail with AttributeError
        max_assets = config.skip.max_items

        self.get_or_create_run_stats().max_assets = max_assets
        self._save_to_file()
        # If the PerformanceTracker already exists, update its internal value
        perf_tracker = self._get_or_create_perf_tracker()
        assert isinstance(perf_tracker, PerformanceTracker)
        perf_tracker.set_max_assets(max_assets)

    @typechecked
    def _set_skip_n(self) -> None:

        skip_n = self._checkpoint.get_effective_skip_n()
        with self._lock:

            self.get_or_create_run_stats().skip_n = skip_n
            self._save_to_file()
            self._get_or_create_perf_tracker().set_skip_n(skip_n)

    # Event counters are now stored in self._current_stats.event_counters
    def __attrs_post_init__(self) -> None:
        # The folder is already created by get_run_output_dir
        # Reserved global variable _instance is required for singleton pattern
        global _instance  # noqa: F824
        if _instance is not None and _instance is not self:
            # Logging the use of reserved variable
            print(
                "[INFO] Reserved global variable _instance is in use for singleton enforcement."
            )
            raise RuntimeError(
                "StatisticsManager instance already exists. "
                "Use StatisticsManager.get_instance() instead of creating a new one."
            )
        # Logging assignment to reserved global variable
        print("[INFO] Assigning self to reserved global variable _instance.")
        _instance = self
        # Initialize declared attributes
        self._checkpoint = CheckpointManager(stats_manager=self)
        self._tags = TagStatsManager(stats_manager=self)
        self._set_max_assets()
        self._set_skip_n()

    @typechecked
    def get_checkpoint_manager(self) -> CheckpointManager:
        return self._checkpoint

    @typechecked
    def increment_event(
        self, event_kind: "ModificationKind", extra_key: "TagWrapper | None" = None
    ) -> None:
        """
        Increment the counter for the given event kind (ModificationKind).
        If extra_key (TagWrapper) is provided, it is concatenated to the event_kind name
        for per-key statistics.
        """
        with self._lock:

            self.get_or_create_run_stats().increment_event(
                event_kind, extra_key=extra_key
            )

    @typechecked
    def get_progress_description(self) -> str:
        count = self.get_or_create_run_stats().count
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. "
                "Call set_total_assets or set_max_assets before processing."
            )
        return self._get_or_create_perf_tracker().get_progress_description(count)

    @typechecked
    def set_total_assets(self, total_assets: int) -> None:
        with self._lock:
            self.get_or_create_run_stats().total_assets = total_assets
            self._save_to_file()
            self._get_or_create_perf_tracker()

    def maybe_print_progress(self, count: int) -> None:
        self._get_or_create_perf_tracker().update(count)

    @typechecked
    def print_progress(self, count: int) -> None:
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker not initialized: totals missing. "
                "Call set_total_assets or set_max_assets before processing."
            )
        self._get_or_create_perf_tracker().print_progress(count=count)

    @staticmethod
    def get_instance() -> "StatisticsManager":
        # Reserved global variable _instance is required for singleton pattern
        global _instance
        if _instance is None:
            # Logging the use of reserved variable
            print(
                "[INFO] Reserved global variable _instance is None, creating new instance."
            )
            StatisticsManager()
        if _instance is None:
            raise RuntimeError("StatisticsManager instance not initialized.")
        return _instance

    @typechecked
    def get_or_create_run_stats(
        self, initial_stats: Optional[RunStatistics] = None
    ) -> RunStatistics:
        # TODO: refactor to get_s
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
                album_date_mismatch_count=0,
                update_asset_date_count=0,
                total_assets=None,
                max_assets=None,
                skip_n=None,
                started_at=None,
                finished_at=None,
                abrupt_exit_at=None,
                # Can be None if there is no previous data; better than inventing a zero
                previous_sessions_time=None,
                extra={},
                output_tag_counters={},
                output_album_counters={},
                progress_description=None,
                event_counters={},
            )
            self._current_stats.save_to_file()
            return self._current_stats

    @typechecked
    def get_stats(self) -> RunStatistics:

        return self.get_or_create_run_stats()

    @typechecked
    def update_checkpoint(
        self, *, last_processed_id: AssetUUID, count: int
    ) -> RunStatistics:
        with self._lock:

            self.get_or_create_run_stats().last_processed_id = str(last_processed_id)
            self.get_or_create_run_stats().count = count
            # Only save to disk every 100 assets (not every asset) for performance
            if count % 100 == 0:
                self._save_to_file()
        self.maybe_print_progress(count)
        return self.get_or_create_run_stats()

    @typechecked
    def save(self) -> None:
        with self._lock:
            self._save_to_file()

    @typechecked
    def delete_all(self) -> None:
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        log(
            "StatisticsManager.delete_all() is deprecated and should not be used. "
            "Statistics are preserved for logging.",
            level=LogLevel.WARNING,
        )

    @typechecked
    def finish_run(self) -> None:
        from datetime import datetime, timezone

        with self._lock:
            now = datetime.now(timezone.utc)
            self.get_or_create_run_stats().finished_at = now
            # Add the time of this session to the accumulated total
            started_at = self.get_or_create_run_stats().started_at
            if started_at is not None:
                session_time = (now - started_at).total_seconds()
                prev = self.get_or_create_run_stats().previous_sessions_time
                if prev is None:
                    prev = 0.0
                self.get_or_create_run_stats().previous_sessions_time = (
                    prev + session_time
                )
            self._save_to_file()

    @typechecked
    def abrupt_exit(self) -> None:
        self.finish_run()

    @property
    def RELEVANT_TAGS(self):
        from immich_autotag.config.manager import (
            ConfigManager,
        )

        manager = ConfigManager.get_instance()
        config = manager.get_config_or_raise()
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
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None",
    ) -> None:
        self._tags.increment_tag_action(tag, kind, album)

    # Tag/album methods delegated to TagStatsManager
    @typechecked
    def initialize_for_run(self, total_assets: int) -> None:

        self._get_or_create_perf_tracker().set_total_assets(total_assets)

        # Initialize total_assets first so that the PerformanceTracker can be
        # initialized correctly
        self.get_or_create_run_stats().total_assets = total_assets
        self.set_total_assets(total_assets)
