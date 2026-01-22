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
        # --- Datos base ---
        avg = elapsed / count if count else 0
        total_to_process = self.total_to_process
        estimator = self.estimator
        skip_n = self.skip_n or 0
        total_assets = self.total_assets
        estimation_mode = self.estimation_mode

        # Obtener tiempo acumulado de sesiones previas
        try:
            from immich_autotag.statistics.statistics_manager import StatisticsManager

            stats = StatisticsManager.get_instance().get_stats()
            previous_sessions_time = getattr(stats, "previous_sessions_time", 0.0)
        except Exception:
            previous_sessions_time = 0.0

        # --- Cálculos de totales ---
        abs_count = count + skip_n
        abs_total = total_assets if total_assets and total_assets > 0 else None

        # --- Estimaciones de tiempo ---
        if total_to_process and count > 0:
            remaining = total_to_process - count
            if (
                estimation_mode == TimeEstimationMode.EWMA
                and estimator is not None
                and estimator.get_estimated_time_per_asset() > 0
            ):
                ewma = estimator.get_estimated_time_per_asset()
                est_total_session = ewma * total_to_process
                est_remaining_session = ewma * remaining
            else:
                est_total_session = avg * total_to_process
                est_remaining_session = est_total_session - elapsed

            from immich_autotag.utils.perf.estimate_utils import adjust_estimates

            est_total_session, est_remaining_session = adjust_estimates(
                elapsed, est_total_session, est_remaining_session
            )
        else:
            est_total_session = None
            est_remaining_session = None

        # --- Estimaciones absolutas (todas las sesiones) ---
        if abs_total and count > 0:
            est_total_all = avg * abs_total
            est_remaining_all = est_total_all - (previous_sessions_time + elapsed)
            from immich_autotag.utils.perf.estimate_utils import adjust_estimates

            est_total_all, est_remaining_all = adjust_estimates(
                previous_sessions_time + elapsed, est_total_all, est_remaining_all
            )
        else:
            est_total_all = None
            est_remaining_all = None

        # --- Formateo de tiempos ---
        def fmt_time(seconds) -> str:
            if seconds is None:
                return "?"
            if seconds >= 3600:
                return f"{seconds/3600:.1f} h"
            elif seconds >= 60:
                return f"{seconds/60:.1f} min"
            else:
                return f"{seconds:.1f} s"

        # --- Mensaje final ---
        msg = f"Procesados en esta sesión: {count}"
        if total_to_process:
            msg += f" / {total_to_process}"
        msg += "\n"

        msg += f"Procesados desde el inicio: {abs_count}"
        if abs_total:
            msg += f" / {abs_total}"
        msg += "\n"

        if abs_total:
            msg += f"Total de elementos en immich: {abs_total}\n"
        else:
            msg += "Total de elementos en immich: ?\n"

        msg += f"\nTiempo transcurrido en esta sesión: {fmt_time(elapsed)}\n"
        msg += f"Tiempo transcurrido en todas las sesiones: {fmt_time(previous_sessions_time + elapsed)}\n"

        if est_remaining_session is not None:
            msg += f"Tiempo pendiente estimado para esta sesión: {fmt_time(est_remaining_session)}\n"
        else:
            msg += "Tiempo pendiente estimado para esta sesión: ?\n"

        if est_total_all is not None:
            msg += f"Tiempo total estimado de todas las sesiones: {fmt_time(est_total_all)}\n"
        else:
            msg += "Tiempo total estimado de todas las sesiones: ?\n"

        msg += f"Tiempo medio de cada asset: {avg:.3f} s"

        return msg
