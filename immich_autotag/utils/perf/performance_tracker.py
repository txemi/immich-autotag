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

    def _printable_value_avg(self, count: int, elapsed: float) -> float:
        return elapsed / count if count else 0

    def _printable_value_total_to_process(self) -> Optional[int]:
        return self.total_to_process

    def _printable_value_skip_n(self) -> int:
        return self.skip_n or 0

    def _printable_value_total_assets(self) -> Optional[int]:
        return self.total_assets

    def _printable_value_previous_sessions_time(self) -> float:
        try:
            from immich_autotag.statistics.statistics_manager import StatisticsManager
            stats = StatisticsManager.get_instance().get_stats()
            return getattr(stats, "previous_sessions_time", 0.0)
        except Exception:
            return 0.0

    def _printable_value_abs_count(self, count: int) -> int:
        return count + self._printable_value_skip_n()

    def _printable_value_abs_total(self) -> Optional[int]:
        total_assets = self._printable_value_total_assets()
        return total_assets if total_assets and total_assets > 0 else None

    def _printable_value_estimation_mode(self):
        return self.estimation_mode

    def _printable_value_estimator(self):
        return self.estimator

    def _printable_value_est_total_session(self, count: int, elapsed: float) -> Optional[float]:
        total_to_process = self._printable_value_total_to_process()
        estimator = self._printable_value_estimator()
        estimation_mode = self._printable_value_estimation_mode()
        avg = self._printable_value_avg(count, elapsed)
        if total_to_process and count > 0:
            if estimation_mode == TimeEstimationMode.EWMA and estimator is not None and estimator.get_estimated_time_per_asset() > 0:
                ewma = estimator.get_estimated_time_per_asset()
                return ewma * total_to_process
            else:
                return avg * total_to_process
        return None

    def _printable_value_est_remaining_session(self, count: int, elapsed: float) -> Optional[float]:
        total_to_process = self._printable_value_total_to_process()
        estimator = self._printable_value_estimator()
        estimation_mode = self._printable_value_estimation_mode()
        avg = self._printable_value_avg(count, elapsed)
        if total_to_process and count > 0:
            remaining = total_to_process - count
            if estimation_mode == TimeEstimationMode.EWMA and estimator is not None and estimator.get_estimated_time_per_asset() > 0:
                ewma = estimator.get_estimated_time_per_asset()
                return ewma * remaining
            else:
                return avg * total_to_process - elapsed
        return None

    def _printable_value_est_total_all(self, count: int, elapsed: float) -> Optional[float]:
        abs_total = self._printable_value_abs_total()
        avg = self._printable_value_avg(count, elapsed)
        if abs_total and count > 0:
            return avg * abs_total
        return None

    def _printable_value_est_remaining_all(self, count: int, elapsed: float, previous_sessions_time: float) -> Optional[float]:
        abs_total = self._printable_value_abs_total()
        avg = self._printable_value_avg(count, elapsed)
        if abs_total and count > 0:
            return avg * abs_total - (previous_sessions_time + elapsed)
        return None

    def _printable_value_fmt_time(self, seconds) -> str:
        if seconds is None:
            return "?"
        if seconds >= 3600:
            return f"{seconds/3600:.1f} h"
        elif seconds >= 60:
            return f"{seconds/60:.1f} min"
        else:
            return f"{seconds:.1f} s"
    @typechecked
    def _format_perf_progress(self, count: int, elapsed: float) -> str:
        avg = self._printable_value_avg(count, elapsed)
        total_to_process = self._printable_value_total_to_process()
        skip_n = self._printable_value_skip_n()
        total_assets = self._printable_value_total_assets()
        previous_sessions_time = self._printable_value_previous_sessions_time()
        abs_count = self._printable_value_abs_count(count)
        abs_total = self._printable_value_abs_total()
        est_total_session = self._printable_value_est_total_session(count, elapsed)
        est_remaining_session = self._printable_value_est_remaining_session(count, elapsed)
        est_total_all = self._printable_value_est_total_all(count, elapsed)
        est_remaining_all = self._printable_value_est_remaining_all(count, elapsed, previous_sessions_time)

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

        msg += f"\nTiempo transcurrido en esta sesión: {self._printable_value_fmt_time(elapsed)}\n"
        msg += f"Tiempo transcurrido en todas las sesiones: {self._printable_value_fmt_time(previous_sessions_time + elapsed)}\n"

        if est_remaining_session is not None:
            msg += f"Tiempo pendiente estimado para esta sesión: {self._printable_value_fmt_time(est_remaining_session)}\n"
        else:
            msg += "Tiempo pendiente estimado para esta sesión: ?\n"

        if est_total_all is not None:
            msg += f"Tiempo total estimado de todas las sesiones: {self._printable_value_fmt_time(est_total_all)}\n"
        else:
            msg += "Tiempo total estimado de todas las sesiones: ?\n"

        msg += f"Tiempo medio de cada asset: {avg:.3f} s"

        return msg
        if est_total_all is not None:
            msg += f"Tiempo total estimado de todas las sesiones: {fmt_time(est_total_all)}\n"
        else:
            msg += "Tiempo total estimado de todas las sesiones: ?\n"

        msg += f"Tiempo medio de cada asset: {avg:.3f} s"

        return msg
