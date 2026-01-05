from typeguard import typechecked

"""
statistics_manager.py

Core statistics management logic for tracking progress, statistics, and historical runs.
Handles YAML serialization, extensibility, and replaces legacy checkpoint logic.
"""


from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .run_statistics import RunStatistics

STATISTICS_DIR = Path("logs")


from threading import RLock

import attr

# Singleton de módulo
_instance = None


@attr.s(auto_attribs=True, kw_only=True)


class StatisticsManager:
    """
    Singleton manager de estadísticas: gestiona la carga, guardado y actualización de estadísticas de ejecución.
    Solo crea y actualiza un fichero por ejecución.
    """

    stats_dir: Path = STATISTICS_DIR
    _instance: "StatisticsManager" = attr.ib(default=None, init=False, repr=False)
    _lock: RLock = attr.ib(factory=RLock, init=False, repr=False)
    _current_stats: Optional[RunStatistics] = attr.ib(
        default=None, init=False, repr=False
    )
    _current_file: Optional[Path] = attr.ib(default=None, init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        self.stats_dir.mkdir(exist_ok=True) 
        global _instance
        if _instance is not None and _instance is not self:
            raise RuntimeError("StatisticsManager instance already exists. Use StatisticsManager.get_instance() instead of creating a new one.")

        _instance = self

    @staticmethod
    def get_instance() -> "StatisticsManager":
        global _instance
        if _instance is None:
            StatisticsManager()
        return _instance

    @typechecked
    def start_run(self, initial_stats: Optional[RunStatistics] = None) -> None:
        """Inicializa el estado para una nueva ejecución."""
        with self._lock:
            if self._current_stats is not None:
                return  # Ya inicializado
            self._current_stats = initial_stats or RunStatistics(
                last_processed_id=None, count=0
            )
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            self._current_file = self.stats_dir / f"run_statistics_{timestamp}.yaml"
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
    def update(self, **kwargs: Any) -> RunStatistics:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            for k, v in kwargs.items():
                if hasattr(self._current_stats, k):
                    setattr(self._current_stats, k, v)
                else:
                    self._current_stats.extra[k] = v
            self._save_to_file()
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
        for f in self.stats_dir.glob("run_statistics_*.yaml"):
            try:
                f.unlink()
            except Exception as e:
                print(f"[WARN] Could not delete statistics file '{f}': {e}")





    @typechecked
    def process_asset_tags(self, tag_names: list[str]) -> None:
        """
        Procesa la lista de etiquetas de un activo y actualiza los contadores totales de las etiquetas de salida relevantes.
        """
        from immich_autotag.config.user import (
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        )
        relevant = {
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        }
        stats = self.get_stats()
        for tag in relevant:
            if tag in tag_names:
                if tag not in stats.output_tag_counters:
                    from .run_statistics import OutputTagCounter
                    stats.output_tag_counters[tag] = OutputTagCounter()
                stats.output_tag_counters[tag].total += 1
        self._save_to_file()

    @typechecked
    def increment_tag_added(self, tag: str) -> None:
        """
        Incrementa el contador de añadidos para una etiqueta relevante.
        """
        from immich_autotag.config.user import (
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        )
        relevant = {
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        }
        if tag in relevant:
            stats = self.get_stats()
            if tag not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter
                stats.output_tag_counters[tag] = OutputTagCounter()
            stats.output_tag_counters[tag].added += 1
            self._save_to_file()

    @typechecked
    def increment_tag_removed(self, tag: str) -> None:
        """
        Incrementa el contador de eliminados para una etiqueta relevante.
        """
        from immich_autotag.config.user import (
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        )
        relevant = {
            AUTOTAG_CATEGORY_UNKNOWN,
            AUTOTAG_CATEGORY_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_ALBUM_CONFLICT,
            AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        }
        if tag in relevant:
            stats = self.get_stats()
            if tag not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter
                stats.output_tag_counters[tag] = OutputTagCounter()
            stats.output_tag_counters[tag].removed += 1
            self._save_to_file()