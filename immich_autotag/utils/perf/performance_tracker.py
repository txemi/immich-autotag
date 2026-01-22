import time
from typing import Optional

import attr
from typeguard import typechecked

from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode


@typechecked
@attr.s(auto_attribs=True, kw_only=True)
class PerformanceTracker:
    start_time: float = attr.ib(factory=lambda: time.time())
    log_interval: int = 5
    estimator: Optional[AdaptiveTimeEstimator] = None
    estimation_mode: TimeEstimationMode = TimeEstimationMode.LINEAR
    total_to_process: Optional[int] = None
    total_assets: Optional[int] = None
    skip_n: Optional[int] = None
    last_log_time: float = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.last_log_time = self.start_time
        # Strict validation: if something essential is missing, crash
        if self.estimation_mode == TimeEstimationMode.EWMA and self.estimator is None:
            raise ValueError(
                "[PERFORMANCE TRACKER] EWMA mode requires a valid estimator. Cannot initialize the tracker."
            )
        if self.total_to_process is None:
            raise ValueError(
                "[PERFORMANCE TRACKER] total_to_process is not defined. Cannot initialize the tracker."
            )

    @typechecked
    def set_progress_timing(self, start_time: float, log_interval: int = 5):
        self.start_time = start_time
        self.last_log_time = start_time
        self.log_interval = log_interval

    @typechecked
    def update(self, count: int):
        now = time.time()
        # If the tracker is not properly initialized, it should never reach here
        if now - self.last_log_time >= self.log_interval:
            elapsed = now - self.start_time
            self.print_progress(count, elapsed)
            self.last_log_time = now

    @typechecked
    def print_progress(self, count: int, elapsed: Optional[float] = None):
        if elapsed is None:
            elapsed = time.time() - self.start_time
        print("[PERF] " + self._format_perf_progress(count, elapsed))

    @typechecked
    def get_progress_description(self, count: int = 0) -> str:
        """
        Devuelve una descripción textual del progreso actual, incluyendo porcentaje y estimación de tiempo si está disponible.
        """
        elapsed = time.time() - self.start_time
        return self._format_perf_progress(count, elapsed)

    @typechecked
    def _format_perf_progress(self, count: int, elapsed: float) -> str:
        avg = elapsed / count if count else 0
        total_to_process = self.total_to_process
        estimator = self.estimator
        skip_n = self.skip_n or 0
        total_assets = self.total_assets
        estimation_mode = self.estimation_mode
        # Determinar el total real a procesar
        if total_to_process is not None and total_to_process > 0 and count > 0:
            remaining = total_to_process - count
            # Relativo (solo esta sesión)
            if (
                estimation_mode == TimeEstimationMode.EWMA
                and estimator is not None
                and estimator.get_estimated_time_per_asset() > 0
            ):
                ewma = estimator.get_estimated_time_per_asset()
                est_total_rel = ewma * total_to_process
                est_remaining_rel = ewma * remaining
            else:
                est_total_rel = avg * total_to_process
                est_remaining_rel = est_total_rel - elapsed
            from immich_autotag.utils.perf.estimate_utils import adjust_estimates

            est_total_rel, est_remaining_rel = adjust_estimates(
                elapsed, est_total_rel, est_remaining_rel
            )
            percent_rel = (count / total_to_process) * 100

            # Absoluto (incluyendo skip_n)
            percent_abs = None
            abs_count = count + skip_n
            abs_total = total_assets if total_assets and total_assets > 0 else "todos"
            est_total_abs = None
            est_remaining_abs = None
            if isinstance(abs_total, int):
                percent_abs = (abs_count / abs_total) * 100
                est_total_abs = avg * abs_total
                est_remaining_abs = est_total_abs - elapsed
                est_total_abs, est_remaining_abs = adjust_estimates(
                    elapsed, est_total_abs, est_remaining_abs
                )

            def fmt_time(minutes: float) -> str:
                if minutes >= 60:
                    return f"{minutes/60:.1f} h"
                else:
                    return f"{minutes:.1f} min"

            # Obtener tiempo acumulado de sesiones previas
            try:
                from immich_autotag.statistics.statistics_manager import (
                    StatisticsManager,
                )

                stats = StatisticsManager.get_instance().get_stats()
                previous_sessions_time = getattr(stats, "previous_sessions_time", 0.0)
            except Exception:
                previous_sessions_time = 0.0

            tiempo_total = previous_sessions_time + elapsed
            tiempo_total_estimado = previous_sessions_time + est_total_rel

            msg = (
                f"Procesados en esta sesión: {count}/{total_to_process} ({percent_rel:.1f}%) | "
                f"Procesados totales: {abs_count}/{abs_total}"
            )
            if percent_abs is not None:
                msg += f" ({percent_abs:.1f}%)"
            msg += f". Avg: {avg:.3f} s. Tiempo transcurrido (sesión): {fmt_time(elapsed/60)}. "
            msg += f"Tiempo transcurrido (todas las sesiones): {fmt_time(tiempo_total/60)}. "
            # Mostrar tiempo estimado previsto (lineal o EWMA)
            if (
                estimation_mode == TimeEstimationMode.EWMA
                and estimator is not None
                and estimator.get_estimated_time_per_asset() > 0
            ):
                msg += f"Tiempo estimado previsto (EWMA, total): {fmt_time(tiempo_total_estimado/60)}."
            else:
                msg += f"Tiempo estimado previsto (lineal, total): {fmt_time(tiempo_total_estimado/60)}."
            msg += (
                f" Tiempo estimado restante (sesión): {fmt_time(est_remaining_rel/60)}."
            )
            if (
                percent_abs is not None
                and est_remaining_abs is not None
                and est_total_abs is not None
            ):
                msg += f" | Tiempo estimado restante (absoluto): {fmt_time(est_remaining_abs/60)}/{fmt_time(est_total_abs/60)}"
            return msg
        else:
            try:
                from immich_autotag.statistics.statistics_manager import (
                    StatisticsManager,
                )

                stats = StatisticsManager.get_instance().get_stats()
                previous_sessions_time = getattr(stats, "previous_sessions_time", 0.0)
            except Exception:
                previous_sessions_time = 0.0
            return (
                f"Procesados en esta sesión: {count}. Avg por elemento: {avg:.3f} s. "
                f"Tiempo transcurrido (sesión): {elapsed:.1f} s. "
                f"Tiempo transcurrido (todas las sesiones): {((previous_sessions_time+elapsed)/60):.1f} min"
            )
