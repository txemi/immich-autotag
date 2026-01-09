import time
from typing import Optional

import attr
from typeguard import typechecked

from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.print_perf import print_perf
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

    def set_progress_timing(self, start_time: float, log_interval: int = 5):
        self.start_time = start_time
        self.last_log_time = start_time
        self.log_interval = log_interval

    def update(self, count: int):
        now = time.time()
        # If the tracker is not properly initialized, it should never reach here
        if now - self.last_log_time >= self.log_interval:
            elapsed = now - self.start_time
            self.print_progress(count, elapsed)
            self.last_log_time = now

    def print_progress(self, count: int, elapsed: Optional[float] = None):
        if elapsed is None:
            elapsed = time.time() - self.start_time
        print_perf(
            count=count,
            elapsed=elapsed,
            total_to_process=self.total_to_process,
            estimator=self.estimator,
            skip_n=self.skip_n,
            total_assets=self.total_assets,
            estimation_mode=self.estimation_mode,
        )
