import time
from dataclasses import dataclass
from typing import Optional

import attr
from typeguard import typechecked

from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode


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


@attr.s(auto_attribs=True, kw_only=True, slots=True)
class PerformanceTracker:

    _start_time: float = attr.ib(
        init=False,
        factory=lambda: time.time(),
        validator=attr.validators.instance_of(float),
    )
    _log_interval: int = attr.ib(default=5, validator=attr.validators.instance_of(int))
    _estimator: Optional[AdaptiveTimeEstimator] = attr.ib(
        init=False,
        default=None,
        validator=attr.validators.optional(
            attr.validators.instance_of(AdaptiveTimeEstimator)
        ),
    )
    _estimation_mode: TimeEstimationMode = attr.ib(
        init=False,
        default=TimeEstimationMode.LINEAR,
        validator=attr.validators.instance_of(TimeEstimationMode),
    )
    # total_to_process is now always calculated dynamically
    _max_assets: Optional[int] = attr.ib(
        init=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _total_assets: Optional[int] = attr.ib(
        init=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _skip_n: Optional[int] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
    )
    _last_log_time: Optional[float] = attr.ib(
        init=False,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(float)),
    )

    def __attrs_post_init__(self):
        # Strict validation: if something essential is missing, crash
        if self._estimation_mode == TimeEstimationMode.EWMA and self._estimator is None:
            raise ValueError(
                "[PERFORMANCE TRACKER] EWMA mode requires a valid estimator. "
                "Cannot initialize the tracker."
            )
        # --- CRAZY CONDITION IN CONSTRUCTOR ---
        from immich_autotag.config.dev_mode import is_crazy_debug_mode

        if (
            is_crazy_debug_mode()
            and self._total_assets is not None
            and self._total_assets < 1000
        ):
            raise Exception(
                "CRAZY_DEBUG mode: total_assets too low (<100000) during "
                "PerformanceTracker initialization"
            )

    @staticmethod
    def from_args(
        total_assets: Optional[int],
        max_assets: Optional[int],
        skip_n: Optional[int] = 0,
    ) -> "PerformanceTracker":
        """
        Static constructor that initializes the instance with setters, with guards for None values.
        """
        instance = PerformanceTracker()
        if total_assets is not None:
            instance.set_total_assets(total_assets)
        if max_assets is not None:
            instance.set_max_assets(max_assets)
        if skip_n is not None:
            instance.set_skip_n(skip_n)
        return instance

    def set_total_assets(self, value: int) -> None:
        self._total_assets = value

    @staticmethod
    def from_total(total_assets: int) -> "PerformanceTracker":
        """
        Static constructor for PerformanceTracker with total_assets set, using setters for consistency.
        """
        instance = PerformanceTracker()
        instance.set_total_assets(total_assets)
        return instance

    @typechecked
    def set_skip_n(self, value: int) -> None:
        """
        Public setter to update skip_n in a controlled way.
        """
        self._skip_n = value

    @typechecked
    def _printable_value_skip_n(self) -> int:
        return self._skip_n or 0

    @typechecked
    def _calc_total_to_process(self) -> Optional[int]:
        """
        Returns the number of assets to process, using the minimum of max_assets and
        (total_assets - skip_n) if both are set.
        """
        skip_n = self._printable_value_skip_n()
        if self._max_assets is not None and self._total_assets is not None:
            return min(self._max_assets, self._total_assets - skip_n)
        if self._max_assets is not None:
            return self._max_assets
        if self._total_assets is not None:
            return self._total_assets - skip_n
        return None

    def _should_emit_log(self, now: float) -> bool:
        """
        Returns True if enough time has passed since the last log, or if never logged.
        """
        return (
            self._last_log_time is not None
            and now - self._last_log_time >= self._log_interval
        ) or self._last_log_time is None

    @typechecked
    def update(self, count: int):
        now = time.time()
        if self._should_emit_log(now):
            self.print_progress(count=count)
            self._last_log_time = now

    @typechecked
    def _printable_value_avg(self, *, count: int, elapsed: float) -> float:
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
        avg = self._printable_value_avg(count=count, elapsed=elapsed)
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
        from immich_autotag.statistics.statistics_manager import StatisticsManager

        stats = StatisticsManager.get_instance().get_stats().previous_sessions_time
        return stats if stats is not None else 0.0

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
        avg = self._printable_value_avg(count=count, elapsed=elapsed)
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
        abs_total_and_avg = self._printable_value__get_abs_total_and_avg(
            count=count, elapsed=elapsed
        )
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
    def _format_perf_progress(
        self, *, count: int, elapsed: Optional[float] = None
    ) -> str:
        if elapsed is None:
            elapsed = time.time() - self._start_time
        avg = self._printable_value_avg(count=count, elapsed=elapsed)
        total_to_process = self._printable_value_total_to_process()
        skip_n = self._printable_value_skip_n()
        previous_sessions_time = self._printable_value_previous_sessions_time()
        abs_count = self._printable_value_abs_count(count)
        abs_total = self._printable_value_abs_total()

        # --- CRAZY CONDITION ---
        # If mode is CRAZY_DEBUG, abs_total is not None and abs_total < 200000,
        # raise exception
        from immich_autotag.config.dev_mode import is_crazy_debug_mode

        if is_crazy_debug_mode() and abs_total is not None and abs_total < 1000:
            raise Exception("CRAZY_DEBUG mode: abs_total too low (<200000)")

        est_remaining_session = self._printable_value_est_remaining_session(
            count, elapsed
        )
        est_total_all = self._printable_value_est_total_all(count, elapsed)

        from immich_autotag.logging.utils import log_trace

        log_trace(
            f"PROGRESS-LINE: count={count}, total_to_process={total_to_process}, "
            f"abs_count={abs_count}, abs_total={abs_total}, skip_n={skip_n}"
        )

        # Progress line construction
        msg = "Processed:"
        # Show only abs_count if it is equal to count
        if abs_count == count:
            msg += f"{abs_count}"
        else:
            msg += f"{count}/{abs_count}(abs_count)"

        # Show only abs_total if it is equal to total_to_process and exists
        if abs_total and total_to_process and abs_total == total_to_process:
            msg += f"/{abs_total}(abs_total)"
        elif total_to_process:
            msg += f"/{total_to_process}(total_to_process)"
            if abs_total:
                msg += f"/{abs_total}(abs_total)"

        # Percentage (now right after the main counter)
        if abs_total and abs_total > 0:
            percent = 100.0 * abs_count / abs_total
            msg += f" [{percent:.2f}%]"

        # Show skip only if it is different from zero
        if skip_n:
            msg += f" Skip:{skip_n}"

        # Remaining
        if est_remaining_session is not None:
            msg += (
                f" Remaining:{self._printable_value_fmt_time(est_remaining_session)}/"
            )
        else:
            msg += " Remaining:?/"

        # Times: hide one if they are equal (with numerical tolerance)
        elapsed_val = elapsed
        total_elapsed_val = previous_sessions_time + elapsed
        elapsed_str = self._printable_value_fmt_time(elapsed) + "(Elapsed)"
        total_elapsed_str = (
            self._printable_value_fmt_time(total_elapsed_val) + "(TotalElapsed)"
        )
        tolerance = 0.01  # seconds
        if abs(elapsed_val - total_elapsed_val) < tolerance:
            msg += elapsed_str
        else:
            msg += elapsed_str + "/" + total_elapsed_str

        if est_total_all is not None:
            est_total_all_str = (
                self._printable_value_fmt_time(est_total_all) + "(est_total_all)"
            )
            # If it matches any of the previous ones, do not show it
            if (
                est_total_all_str != elapsed_str
                and est_total_all_str != total_elapsed_str
            ):
                msg += f"/{est_total_all_str}"
        else:
            msg += "/?(est_total_all)"

        msg += f" Average: {avg:.3f} s"
        return msg

    @typechecked
    def print_progress(self, *, count: int, elapsed: Optional[float] = None):
        if elapsed is None:
            elapsed = time.time() - self._start_time
        print("[PERF] " + self._format_perf_progress(count=count, elapsed=elapsed))

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
        time estimation if available. If called after should_log_progress, updates
        last_log_time. Mirrors the output of print_progress but as a string.
        """
        elapsed = time.time() - self._start_time
        return self._format_perf_progress(count=count, elapsed=elapsed)

    @typechecked
    def set_max_assets(self, value: int | None) -> None:
        """
        Public setter to update max_assets in a controlled way. Allows None to disable
        the limit.
        """
        self._max_assets = value

    def should_log_progress(self, count: int) -> bool:
        """
        Returns True if a progress log should be emitted for this count, according to
        the internal log interval logic. Updates internal state if True (so that
        get_progress_description can be used externally).
        """
        now = time.time()
        if count == 1 or (self._total_assets and count == self._total_assets):
            self._last_log_time = now
            return True
        if self._should_emit_log(now):
            self._last_log_time = now
            return True
        return False
