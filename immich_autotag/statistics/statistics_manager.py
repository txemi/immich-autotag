from typeguard import typechecked

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper

"""
statistics_manager.py

Core statistics management logic for tracking progress, statistics, and historical runs.
Handles YAML serialization, extensibility, and replaces legacy checkpoint logic.
"""


from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from immich_autotag.tags.modification_kind import ModificationKind
# ...existing code...
from .run_statistics import RunStatistics
from immich_autotag.utils.run_output_dir import get_run_output_dir

from threading import RLock

import attr

from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

# Singleton de módulo
_instance = None


@attr.s(auto_attribs=True, kw_only=True)
class StatisticsManager:

    _perf_tracker: PerformanceTracker = attr.ib(default=None, init=False, repr=False)

    def _try_init_perf_tracker(self):
        if self._perf_tracker is not None:
            return
        total = self._current_stats.total_assets or self._current_stats.max_assets
        if total is not None:
            import time

            from immich_autotag.utils.perf.estimator import \
                AdaptiveTimeEstimator
            from immich_autotag.utils.perf.time_estimation_mode import \
                TimeEstimationMode

            self._perf_tracker = PerformanceTracker(
                start_time=time.time(),
                log_interval=5,
                estimator=AdaptiveTimeEstimator(),
                estimation_mode=TimeEstimationMode.LINEAR,
                total_to_process=total,
                total_assets=self._current_stats.total_assets,
                skip_n=self._current_stats.skip_n,
            )

    def set_total_assets(self, total_assets: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.total_assets = total_assets
            self._save_to_file()
            self._try_init_perf_tracker()

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
                "PerformanceTracker no inicializado: faltan totales. Llama a set_total_assets o set_max_assets antes de procesar."
            )
        self._perf_tracker.update(count)

    def print_progress(self, count: int) -> None:
        if self._perf_tracker is None:
            raise RuntimeError(
                "PerformanceTracker no inicializado: faltan totales. Llama a set_total_assets o set_max_assets antes de procesar."
            )
        self._perf_tracker.print_progress(count)

    stats_dir: Path = attr.ib(factory=get_run_output_dir, init=False, repr=False)
    _instance: "StatisticsManager" = attr.ib(default=None, init=False, repr=False)
    _lock: RLock = attr.ib(factory=RLock, init=False, repr=False)
    _current_stats: Optional[RunStatistics] = attr.ib(
        default=None, init=False, repr=False
    )
    _current_file: Optional[Path] = attr.ib(default=None, init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        # La carpeta ya la crea get_run_output_dir
        global _instance
        if _instance is not None and _instance is not self:
            raise RuntimeError(
                "StatisticsManager instance already exists. Use StatisticsManager.get_instance() instead of creating a new one."
            )
        _instance = self

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
            self._current_stats = initial_stats or RunStatistics(
                last_processed_id=None, count=0
            )
            self._current_file = self.stats_dir / "run_statistics.yaml"
            self._save_to_file()

    def _save_to_file(self) -> None:
        if self._current_stats and self._current_file:
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
            self._save_to_file()
        self.maybe_print_progress(count)
        return self._current_stats

    @typechecked
    def save(self) -> None:
        with self._lock:
            self._save_to_file()

    @typechecked
    def load_latest(self) -> Optional[RunStatistics]:
        files = sorted(self.stats_dir.glob("run_statistics_*.yaml"), reverse=True)
        if files:
            with open(files[0], "r", encoding="utf-8") as f:
                stats = RunStatistics.from_yaml(f.read())
                return stats
        return None

    @typechecked
    def delete_all(self) -> None:
        print(
            "[WARN] StatisticsManager.delete_all() está obsoleto y no debe usarse. Las estadísticas se conservan para registro."
        )

    @typechecked
    def finish_run(self) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            from datetime import datetime, timezone

            self._current_stats.finished_at = datetime.now(timezone.utc)
            self._save_to_file()

    from immich_autotag.config.user import (
        AUTOTAG_CATEGORY_CONFLICT, AUTOTAG_CATEGORY_UNKNOWN,
        AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
        AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT)

    RELEVANT_TAGS = {
        AUTOTAG_CATEGORY_UNKNOWN,
        AUTOTAG_CATEGORY_CONFLICT,
        AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
        AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
    }

    @typechecked
    def process_asset_tags(self, tag_names: list[str]) -> None:
        stats = self.get_stats()
        for tag in self.RELEVANT_TAGS:
            if tag in tag_names:
                if tag not in stats.output_tag_counters:
                    from .run_statistics import OutputTagCounter

                    stats.output_tag_counters[tag] = OutputTagCounter()
                stats.output_tag_counters[tag].total += 1
        self._save_to_file()

    @typechecked
    def increment_tag_added(self, tag: "TagWrapper") -> None:
        tag_name = tag.name
        if tag_name in self.RELEVANT_TAGS:
            stats = self.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter
                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].added += 1
            self._save_to_file()

    @typechecked
    def increment_tag_removed(self, tag: "TagWrapper") -> None:
        # Enforce TagWrapper type
        if not hasattr(tag, "name"):
            raise TypeError(f"increment_tag_removed expects TagWrapper, got {type(tag)}: {tag}")
        tag_name = tag.name
        if tag_name in self.RELEVANT_TAGS:
            stats = self.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter
                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].removed += 1
            self._save_to_file()

    @typechecked
    def set_skip_n(self, skip_n: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.skip_n = skip_n
            self._save_to_file()

    @typechecked
    def get_effective_skip_n(self) -> tuple[str | None, int]:
        from immich_autotag.config.user import ENABLE_CHECKPOINT_RESUME
        from immich_autotag.logging.levels import LogLevel
        from immich_autotag.logging.utils import log

        OVERLAP = 100
        if ENABLE_CHECKPOINT_RESUME:
            stats = self.load_latest()
            if stats:
                last_processed_id, skip_n = stats.last_processed_id, stats.count
            else:
                last_processed_id, skip_n = None, 0
            if skip_n > 0:
                adjusted_skip_n = max(0, skip_n - OVERLAP)
                if adjusted_skip_n != skip_n:
                    log(
                        f"[CHECKPOINT] Overlapping: skip_n adjusted from {skip_n} to {adjusted_skip_n} (overlap {OVERLAP})",
                        level=LogLevel.PROGRESS,
                    )
                else:
                    log(
                        f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id}).",
                        level=LogLevel.PROGRESS,
                    )
                skip_n = adjusted_skip_n
            else:
                log(
                    f"[CHECKPOINT] Will skip {skip_n} assets (from checkpoint: id={last_processed_id}).",
                    level=LogLevel.PROGRESS,
                )
        else:
            last_processed_id, skip_n = None, 0
            log(
                "[CHECKPOINT] Checkpoint resume is disabled. Starting from the beginning.",
                level=LogLevel.PROGRESS,
            )
        self.set_skip_n(skip_n)
        return last_processed_id, skip_n
    @typechecked
    def increment_tag_action(
        self,
        tag: "TagWrapper",
        kind: "ModificationKind",
        album: "AlbumResponseWrapper | None" ,
    ) -> None:
        """
        album: AlbumResponseWrapper o None. Solo se usa para casos de álbum (ej: ASSIGN_ASSET_TO_ALBUM).
        """
        # Local import to avoid UnboundLocalError and cyclic import

        from immich_autotag.tags.modification_kind import ModificationKind
        if kind == ModificationKind.ADD_TAG_TO_ASSET:
            self.increment_tag_added(tag)
        elif kind == ModificationKind.REMOVE_TAG_FROM_ASSET:
            self.increment_tag_removed(tag)
        elif kind == ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED:
            # Count as error for this tag
            tag_name = tag.name
            stats = self.get_stats()
            if tag_name not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter
                stats.output_tag_counters[tag_name] = OutputTagCounter()
            stats.output_tag_counters[tag_name].errors += 1
            self._save_to_file()
        elif kind == ModificationKind.UPDATE_ASSET_DATE:
            # Count asset date updates globally
            stats = self.get_stats()
            stats.update_asset_date_count += 1
            self._save_to_file()
        elif kind == ModificationKind.ASSIGN_ASSET_TO_ALBUM:
            # Contar asignaciones de assets a álbumes usando output_album_counters
            if album is not None:
                assert isinstance(album, AlbumResponseWrapper)
                album_name = album.album.name
                stats = self.get_stats()
                if album_name not in stats.output_album_counters:
                    from .run_statistics import OutputAlbumCounter
                    stats.output_album_counters[album_name] = OutputAlbumCounter()
                stats.output_album_counters[album_name].assigned += 1
                stats.output_album_counters[album_name].total += 1
                self._save_to_file()
            else:
                # Si no se pasa album, no se puede contar
                raise RuntimeError(
                    "AlbumResponseWrapper es requerido para contar ASSIGN_ASSET_TO_ALBUM"
                )
        else:
            # Si se requiere, agregar otros casos aquí
            raise NotImplementedError(
                f"increment_tag_action no implementado para ModificationKind: {kind}"
            )