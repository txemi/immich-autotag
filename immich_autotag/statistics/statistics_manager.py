
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

        def print_progress(
            self,
            count: int,
            elapsed: float,
            total_to_process: Optional[int] = None,
            estimator: Optional[Any] = None,
            skip_n: Optional[int] = None,
            total_assets: Optional[int] = None,
            estimation_mode: Any = None,
        ) -> None:
            """
            Llama al gestor de rendimiento para imprimir el progreso actual.
            No mueve lógica, solo centraliza la llamada.
            """
            from immich_autotag.utils.perf.print_perf import print_perf
            print_perf(
                count=count,
                elapsed=elapsed,
                total_to_process=total_to_process,
                estimator=estimator,
                skip_n=skip_n,
                total_assets=total_assets,
                estimation_mode=estimation_mode,
            )
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
    def update_checkpoint(self, last_processed_id: str, count: int) -> RunStatistics:
        """
        Actualiza el checkpoint de procesamiento (último id procesado y contador).
        """
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.last_processed_id = last_processed_id
            self._current_stats.count = count
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
        """
        [OBSOLETO] Ya no se deben eliminar estadísticas. Se mantiene solo por compatibilidad.
        """
        print(
            "[WARN] StatisticsManager.delete_all() está obsoleto y no debe usarse. Las estadísticas se conservan para registro."
        )

    @typechecked
    def finish_run(self) -> None:
        """
        Marca la fecha de finalización de la ejecución en las estadísticas.
        """
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            from datetime import datetime, timezone

            self._current_stats.finished_at = datetime.now(timezone.utc)
            self._save_to_file()

    # Tags relevantes para estadísticas (atributo de clase)
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
        """
        Procesa la lista de etiquetas de un activo y actualiza los contadores totales de las etiquetas de salida relevantes.
        """
        stats = self.get_stats()
        for tag in self.RELEVANT_TAGS:
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
        if tag in self.RELEVANT_TAGS:
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
        if tag in self.RELEVANT_TAGS:
            stats = self.get_stats()
            if tag not in stats.output_tag_counters:
                from .run_statistics import OutputTagCounter

                stats.output_tag_counters[tag] = OutputTagCounter()
            stats.output_tag_counters[tag].removed += 1
            self._save_to_file()

    @typechecked
    def set_total_assets(self, total_assets: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.total_assets = total_assets
            self._save_to_file()

    @typechecked
    def set_max_assets(self, max_assets: int) -> None:
        with self._lock:
            if self._current_stats is None:
                self.start_run()
            self._current_stats.max_assets = max_assets
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
        """
        Devuelve el (last_processed_id, skip_n) efectivo según la configuración de usuario y el estado previo.
        Si ENABLE_CHECKPOINT_RESUME está activo y hay estado previo, lo usa; si no, devuelve (None, 0).
        Aplica la lógica de overlap si corresponde.
        Además, sincroniza y persiste skip_n en el estado actual para que quede reflejado en el fichero de estadísticas.
        """
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
        # Sincroniza y persiste skip_n en el estado actual
        self.set_skip_n(skip_n)
        return last_processed_id, skip_n