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
    def _printable_value__get_abs_total_and_avg(
        self, count: int, elapsed: float
    ) -> tuple[Optional[int], float]:
        """Returns abs_total and avg for methods that use them together."""
        abs_total = self._printable_value_abs_total()
        avg = self._printable_value_avg(count, elapsed)
        return abs_total, avg

    @typechecked
    def _printable_value__get_remaining(self, count: int) -> Optional[int]:
        total_to_process = self._printable_value_total_to_process()
        if total_to_process is not None:
            return total_to_process - count
        return None

    @typechecked
    def _printable_value_avg(self, count: int, elapsed: float) -> float:
        return elapsed / count if count else 0

    @typechecked
    def _printable_value_total_to_process(self) -> Optional[int]:
        return self.total_to_process

    @typechecked
    def _printable_value_skip_n(self) -> int:
        return self.skip_n or 0

    @typechecked
    def _printable_value_total_assets(self) -> Optional[int]:
        return self.total_assets

    @typechecked
    def _printable_value_previous_sessions_time(self) -> float:
        try:
            from immich_autotag.statistics.statistics_manager import StatisticsManager
            stats = StatisticsManager.get_instance().get_stats()
            return getattr(stats, "previous_sessions_time", 0.0)
        except Exception:
            return 0.0

    @typechecked
    def _printable_value_abs_count(self, count: int) -> int:
        return count + self._printable_value_skip_n()

    @typechecked
    def _printable_value_abs_total(self) -> Optional[int]:
        total_assets = self._printable_value_total_assets()
        return total_assets if total_assets and total_assets > 0 else None

    @typechecked
    def _printable_value_estimation_mode(self) -> TimeEstimationMode:
        return self.estimation_mode

    @typechecked
    def _printable_value_estimator(self) -> Optional[AdaptiveTimeEstimator]:
        return self.estimator

    def _printable_value__get_avg_and_totals(self, count: int, elapsed: float):
        avg = self._printable_value_avg(count, elapsed)
        total_to_process = self._printable_value_total_to_process()
        estimator = self._printable_value_estimator()
        estimation_mode = self._printable_value_estimation_mode()
        return avg, total_to_process, estimator, estimation_mode

    @typechecked
    def _printable_value_est_total_session(
        self, count: int, elapsed: float
    ) -> Optional[float]:
        avg, total_to_process, estimator, estimation_mode = (
            self._printable_value__get_avg_and_totals(count, elapsed)
        )
        if total_to_process and count > 0:
            if (
                estimation_mode == TimeEstimationMode.EWMA
                and estimator is not None
                and estimator.get_estimated_time_per_asset() > 0
            ):
                ewma = estimator.get_estimated_time_per_asset()
                return ewma * total_to_process
            else:
                return avg * total_to_process
        return None

    @typechecked
    def _printable_value_est_remaining_session(
        self, count: int, elapsed: float
    ) -> Optional[float]:
        avg, total_to_process, estimator, estimation_mode = (
            self._printable_value__get_avg_and_totals(count, elapsed)
        )
        remaining = self._printable_value__get_remaining(count)
        if total_to_process and count > 0 and remaining is not None:
            if (
                estimation_mode == TimeEstimationMode.EWMA
                and estimator is not None
                and estimator.get_estimated_time_per_asset() > 0
            ):
                ewma = estimator.get_estimated_time_per_asset()
                return ewma * remaining
            else:
                return avg * total_to_process - elapsed
        return None

    @typechecked
    def _printable_value_est_total_all(
        self, count: int, elapsed: float
    ) -> Optional[float]:
        abs_total, avg = self._printable_value__get_abs_total_and_avg(count, elapsed)
        if abs_total and count > 0:
            return avg * abs_total
        return None

    @typechecked
    def _printable_value_est_remaining_all(
        self, count: int, elapsed: float, previous_sessions_time: float
    ) -> Optional[float]:
        abs_total, avg = self._printable_value__get_abs_total_and_avg(count, elapsed)
        if abs_total and count > 0:
            return avg * abs_total - (previous_sessions_time + elapsed)
        return None

    @typechecked
    def _printable_value_fmt_time(self, seconds: Optional[float]) -> str:
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
        est_remaining_session = self._printable_value_est_remaining_session(
            count, elapsed
        )
        est_total_all = self._printable_value_est_total_all(count, elapsed)
        est_remaining_all = self._printable_value_est_remaining_all(
            count, elapsed, previous_sessions_time
        )

        msg = f"Processed in this session: {count}"
        if total_to_process:
            msg += f" / {total_to_process}"
        msg += "\n"

        msg += f"Processed since start: {abs_count}"
        if abs_total:
            msg += f" / {abs_total}"
        msg += "\n"

        if abs_total:
            msg += f"Total elements in immich: {abs_total}\n"
        else:
            msg += "Total elements in immich: ?\n"

        msg += f"\nElapsed time in this session: {self._printable_value_fmt_time(elapsed)}\n"
        msg += f"Elapsed time in all sessions: {self._printable_value_fmt_time(previous_sessions_time + elapsed)}\n"

        if est_remaining_session is not None:
            msg += f"Estimated remaining time for this session: {self._printable_value_fmt_time(est_remaining_session)}\n"
        else:
            msg += "Estimated remaining time for this session: ?\n"

        if est_total_all is not None:
            msg += f"Estimated total time for all sessions: {self._printable_value_fmt_time(est_total_all)}\n"
        else:
            msg += "Estimated total time for all sessions: ?\n"

        msg += f"Average time per asset: {avg:.3f} s"

        return msg
