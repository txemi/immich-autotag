"""
statistics_manager.py

Core statistics management logic for tracking progress, statistics, and historical runs.
Handles YAML serialization, extensibility, and replaces legacy checkpoint logic.
"""

from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, Optional

import attr
import git
from typeguard import typechecked

from immich_autotag.config.models import UserConfig  # GitPython
from immich_autotag.types.uuid_wrappers import AssetUUID
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
    # By convention, the constructor arguments for classes using attrs should be
    # public (no leading underscore), even if the internal attributes are private
    # (with leading underscore). attrs requires this to function correctly.
    # If the linter (e.g., flake8, pylint, mypy) complains about the mismatch
    # between public arguments and private attributes, silence the warning with a
    # noqa or specific configuration, as this is the correct pattern with attrs.
    # Example: pylint: disable=attribute-defined-outside-init
    #
    # Reference: https://www.attrs.org/en/stable/init.html#private-attributes
    _perf_tracker: Optional[PerformanceTracker] = attr.ib(
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

        self._perf_tracker = PerformanceTracker.from_args(
            total_assets,
            max_assets=max_assets,
            skip_n=self.get_or_create_run_stats().skip_n,
        )
        return self._perf_tracker

    @typechecked
    def _set_skip_n(self) -> None:

        skip_n = self._checkpoint.get_effective_skip_n()
        with self._lock:

            self.get_or_create_run_stats().skip_n = skip_n
            self.save_to_file()
            self._get_or_create_perf_tracker().set_skip_n(skip_n)

    def _update_perf_tracker_max_assets(self, max_assets: int | None) -> None:
        """
        Update the value of max_assets in the PerformanceTracker if it exists.
        """
        perf_tracker = self._get_or_create_perf_tracker()
        assert isinstance(perf_tracker, PerformanceTracker)
        perf_tracker.set_max_assets(max_assets)

    def _update_stats_max_assets(self) -> int | None:
        """
        Update the value of max_assets in the statistics and save the changes.
        """
        from immich_autotag.config.manager import ConfigManager

        max_assets = ConfigManager.get_effective_max_items()
        self.get_or_create_run_stats().max_assets = max_assets
        self.save_to_file()
        return max_assets

    def _refresh_max_assets(self) -> int | None:
        """
        Refresh the value of max_assets from the effective configuration and update it in the statistics.
        """
        max_assets: int | None = self._update_stats_max_assets()
        if max_assets is not None:
            self._update_perf_tracker_max_assets(max_assets)
        return max_assets

    # Event counters are now stored in self._current_stats.event_counters
    def __attrs_post_init__(self) -> None:
        # The folder is already created by get_run_output_dir
        # Singleton pattern: prevent direct instantiation when already instantiated
        global _instance
        if _instance is not None and _instance is not self:
            # Logging the use of reserved variable
            print(
                "[INFO] Reserved global variable _instance is in use for "
                "singleton enforcement."
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
        self._tags = TagStatsManager(self)
        self._refresh_max_assets()
        self._set_skip_n()

    def save_to_file(self) -> None:
        if self._current_stats and self._current_file:
            # Always update progress_description before saving
            self.get_or_create_run_stats().progress_description = (
                self.get_progress_description()
            )
            self.get_or_create_run_stats().save_to_file()

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
            self.save_to_file()
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
        if _instance is None:
            # Logging the use of reserved variable
            print(
                "[INFO] Reserved global variable _instance is None, "
                "creating new instance."
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
                self.save_to_file()
        self.maybe_print_progress(count)
        return self.get_or_create_run_stats()

    @typechecked
    def save(self) -> None:
        with self._lock:
            self.save_to_file()

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
            self.save_to_file()

    @typechecked
    def abrupt_exit(self) -> None:
        self.finish_run()

    def get_relevant_tags(self) -> set[str]:
        from immich_autotag.config.manager import ConfigManager

        manager: ConfigManager = ConfigManager.get_instance()
        config: UserConfig = manager.get_config_or_raise()
        tags: set[str] = set()
        # Always add classification tags if not None
        if config.classification.autotag_unknown is not None:
            tags.add(config.classification.autotag_unknown)
        if config.classification.autotag_conflict is not None:
            tags.add(config.classification.autotag_conflict)
        # Defensive: duplicate_processing may be None, but if present, we know its type
        if config.duplicate_processing is not None:
            if config.duplicate_processing.autotag_album_conflict is not None:
                tags.add(config.duplicate_processing.autotag_album_conflict)
            if config.duplicate_processing.autotag_classification_conflict is not None:
                tags.add(config.duplicate_processing.autotag_classification_conflict)
        return tags

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

    def get_max_assets(self) -> int | None:
        """
        Returns the updated value of max_assets, applying refresh logic if necessary.
        """
        # Here you can add logic to refresh from config if needed
        # or to synchronize with the effective value
        max_assets = self._refresh_max_assets()
        return max_assets
