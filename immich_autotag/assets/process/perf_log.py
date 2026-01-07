from __future__ import annotations

from typeguard import typechecked

from immich_autotag.utils.perf.estimator import AdaptiveTimeEstimator
from immich_autotag.utils.perf.print_perf import print_perf
from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode


@typechecked
def perf_log(
    count: int,
    elapsed: float,
    estimator: AdaptiveTimeEstimator,
    total_to_process: int | None,
    skip_n: int,
    total_assets: int | None,
) -> None:
    print_perf(
        count,
        elapsed,
        total_to_process,
        estimator,
        skip_n=skip_n if skip_n else 0,
        total_assets=total_assets,
        estimation_mode=TimeEstimationMode.LINEAR,
    )
