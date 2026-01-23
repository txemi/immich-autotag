import time
from dataclasses import dataclass
from typing import Optional

import attr
from typeguard import typechecked

from immich_autotag.logging.utils import log_debug
from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode


# --- Tuple replacement dataclasses ---
@dataclass
class AbsTotalAndAvg:
    abs_total: Optional[int]
    avg: float


@dataclass
class AvgAndTotals:
    avg: float
    total_to_process: Optional[int]
    estimator: Optional[AdaptiveTimeEstimator]
    estimation_mode: TimeEstimationMode


@typechecked
@attr.s(auto_attribs=True, kw_only=True, slots=True)
class PerformanceTracker:

    _start_time: float = attr.ib(
        factory=lambda: time.time(), validator=attr.validators.instance_of(float)
    )
    _log_interval: int = attr.ib(default=5, validator=attr.validators.instance_of(int))
    _estimator: Optional[AdaptiveTimeEstimator] = attr.ib(
        default=None,
        validator=attr.validators.optional(
            attr.validators.instance_of(AdaptiveTimeEstimator)
        ),
    )
    _estimation_mode: TimeEstimationMode = attr.ib(
        default=TimeEstimationMode.LINEAR,
        validator=attr.validators.instance_of(TimeEstimationMode),
    )
    # total_to_process is now always calculated dynamically
    _max_assets: Optional[int] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _total_assets: Optional[int] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _skip_n: Optional[int] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _last_log_time: float = attr.ib(
        init=False, validator=attr.validators.instance_of(float)
    )

    def __attrs_post_init__(self):
        self._last_log_time = self._start_time
        # Strict validation: if something essential is missing, crash
        if self._estimation_mode == TimeEstimationMode.EWMA and self._estimator is None:
            raise ValueError(
                "[PERFORMANCE TRACKER] EWMA mode requires a valid estimator. Cannot initialize the tracker."
            )

    @typechecked
    def set_skip_n(self, value: int) -> None:
        """
        Public setter to update skip_n in a controlled way.
        """
        self._skip_n = value

    @typechecked
    def set_total_assets(self, value: int):
        self._total_assets = value

    @typechecked
    def _printable_value_skip_n(self) -> int:
        return self._skip_n or 0

    @typechecked
    def _calc_total_to_process(self) -> Optional[int]:
        """
        Returns the number of assets to process, using the minimum of max_assets and (total_assets - skip_n) if both are set.
        """
        skip_n = self._printable_value_skip_n()
        if self._max_assets is not None and self._total_assets is not None:
            return min(self._max_assets, self._total_assets - skip_n)
        if self._max_assets is not None:
            return self._max_assets
        if self._total_assets is not None:
            return self._total_assets - skip_n
        return None

    @typechecked
    def update(self, count: int):
        now = time.time()
        # If the tracker is not properly initialized, it should never reach here
        if now - self._last_log_time >= self._log_interval:
            elapsed = now - self._start_time
            self.print_progress(count, elapsed)
            self._last_log_time = now

    @typechecked
    def _printable_value_avg(self, count: int, elapsed: float) -> float:
        return elapsed / count if count else 0

    @typechecked
    def _printable_value_abs_total(self) -> Optional[int]:
        if self._total_assets and self._total_assets > 0:
            return self._total_assets
        return None

    @typechecked
    def _printable_value__get_abs_total_and_avg(
        self, count: int, elapsed: float
    ) -> AbsTotalAndAvg:
        """Returns abs_total and avg for methods that use them together."""
        abs_total = self._printable_value_abs_total()
        avg = self._printable_value_avg(count, elapsed)
        return AbsTotalAndAvg(abs_total=abs_total, avg=avg)

    @typechecked
    def _printable_value_total_to_process(self) -> Optional[int]:
        return self._calc_total_to_process()

    @typechecked
    def _printable_value__get_remaining(self, count: int) -> Optional[int]:
        total_to_process = self._printable_value_total_to_process()
        if total_to_process is not None:
            return total_to_process - count
        return None

    @typechecked
    def _printable_value_previous_sessions_time(self) -> float:
        try:
            from immich_autotag.statistics.statistics_manager import StatisticsManager

            stats = StatisticsManager.get_instance().get_stats()
            try:
                return stats.previous_sessions_time
            except AttributeError:
                return 0.0
        except Exception:
            return 0.0

    @typechecked
    def _printable_value_abs_count(self, count: int) -> int:
        return count + self._printable_value_skip_n()

    @typechecked
    def _printable_value_estimation_mode(self) -> TimeEstimationMode:
        return self._estimation_mode

    @typechecked
    def _printable_value_estimator(self) -> Optional[AdaptiveTimeEstimator]:
        return self._estimator

    def _printable_value__get_avg_and_totals(
        self, count: int, elapsed: float
    ) -> AvgAndTotals:
        avg = self._printable_value_avg(count, elapsed)
        total_to_process = self._printable_value_total_to_process()
        estimator = self._printable_value_estimator()
        estimation_mode = self._printable_value_estimation_mode()
        return AvgAndTotals(
            avg=avg,
            total_to_process=total_to_process,
            estimator=estimator,
            estimation_mode=estimation_mode,
        )

    @typechecked
    def _printable_value_est_remaining_session(
        self, count: int, elapsed: float
    ) -> Optional[float]:
        avg_and_totals = self._printable_value__get_avg_and_totals(count, elapsed)
        avg = avg_and_totals.avg
        total_to_process = avg_and_totals.total_to_process
        estimator = avg_and_totals.estimator
        estimation_mode = avg_and_totals.estimation_mode
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
        abs_total_and_avg = self._printable_value__get_abs_total_and_avg(count, elapsed)
        abs_total = abs_total_and_avg.abs_total
        avg = abs_total_and_avg.avg
        if abs_total and count > 0:
            return avg * abs_total
        return None

    @typechecked
    def _printable_value_fmt_time(self, seconds: Optional[float]) -> str:
        if seconds is None:
            return "?"
        if seconds >= 3600:
            return f"{seconds/3600:.1f}h"
        elif seconds >= 60:
            return f"{seconds/60:.1f}min"
        else:
            return f"{seconds:.1f}s"

    @typechecked
    def _format_perf_progress(self, count: int, elapsed: float) -> str:

        avg = self._printable_value_avg(count, elapsed)
        total_to_process = self._printable_value_total_to_process()
        skip_n = self._printable_value_skip_n()
        # Removed unused variable assignment for total_assets
        previous_sessions_time = self._printable_value_previous_sessions_time()
        abs_count = self._printable_value_abs_count(count)
        abs_total = self._printable_value_abs_total()
        # est_total_session = self._printable_value_est_total_session(count, elapsed)  # Unused
        est_remaining_session = self._printable_value_est_remaining_session(
            count, elapsed
        )
        est_total_all = self._printable_value_est_total_all(count, elapsed)
        # est_remaining_all = self._printable_value_est_remaining_all(count, elapsed, previous_sessions_time)  # Unused

        log_debug(
            f"PROGRESS-LINE: count={count}, total_to_process={total_to_process}, "
            f"abs_count={abs_count}, abs_total={abs_total}, skip_n={skip_n}"
        )
        msg = f"Processed:{count}"
        if total_to_process:
            msg += f"/{total_to_process}(total_to_process)"

        msg += f"/{abs_count}(abs_count)"
        if abs_total:
            msg += f"/{abs_total}(abs_total)"

        # Always print skip_n
        msg += f" Skip:{skip_n}"

        # Progress percentage
        if abs_total and abs_total > 0:
            percent = 100.0 * abs_count / abs_total
            msg += f" [{percent:.2f}%]"

        if est_remaining_session is not None:
            msg += (
                f" Remaining:{self._printable_value_fmt_time(est_remaining_session)}/"
            )
        else:
            msg += " Remaining:?/"

        msg += f"{self._printable_value_fmt_time(elapsed)}(Elapsed)"
        msg += (
            f"/{self._printable_value_fmt_time(previous_sessions_time + elapsed)}"
            "(TotalElapsed)"
        )

        if est_total_all is not None:
            msg += f"/{self._printable_value_fmt_time(est_total_all)}(est_total_all)"
        else:
            msg += "/?(est_total_all)"

        msg += f" Average: {avg:.3f} s"

        return msg

    @typechecked
    def print_progress(self, count: int, elapsed: Optional[float] = None):
        if elapsed is None:
            elapsed = time.time() - self._start_time
        print("[PERF] " + self._format_perf_progress(count, elapsed))

    @typechecked
    def _printable_value_total_assets(self) -> Optional[int]:
        return self._total_assets

    @typechecked
    def _printable_value_est_total_session(
        self, count: int, elapsed: float
    ) -> Optional[float]:
        avg_and_totals = self._printable_value__get_avg_and_totals(count, elapsed)
        avg = avg_and_totals.avg
        total_to_process = avg_and_totals.total_to_process
        estimator = avg_and_totals.estimator
        estimation_mode = avg_and_totals.estimation_mode
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
    def _printable_value_est_remaining_all(
        self, count: int, elapsed: float, previous_sessions_time: float
    ) -> Optional[float]:
        abs_total_and_avg = self._printable_value__get_abs_total_and_avg(count, elapsed)
        abs_total = abs_total_and_avg.abs_total
        avg = abs_total_and_avg.avg
        if abs_total and count > 0:
            return avg * abs_total - (previous_sessions_time + elapsed)
        return None

    @typechecked
    def get_progress_description(self, count: int) -> str:
        """
        Returns a textual description of current progress, including percentage and
        time estimation if available.
        Mirrors the output of print_progress but as a string.
        """
        elapsed = time.time() - self._start_time
        return self._format_perf_progress(count, elapsed)

    def set_max_assets(self, value: int | None) -> None:
        """
        Public setter to update max_assets in a controlled way. Allows None to disable the limit.
        """
        self._max_assets = value
