from typing import Optional

from typeguard import typechecked

from immich_autotag.utils.perf.time_estimation_mode import TimeEstimationMode

from .estimate_utils import adjust_estimates
from .estimator import AdaptiveTimeEstimator


@typechecked
def format_perf_progress(
    count: int,
    elapsed: float,
    total_to_process: Optional[int] = None,
    estimator: Optional[AdaptiveTimeEstimator] = None,
    skip_n: Optional[int] = None,
    total_assets: Optional[int] = None,
    estimation_mode: TimeEstimationMode = TimeEstimationMode.LINEAR,
) -> str:
    avg = elapsed / count if count else 0
    if total_to_process and count > 0:
        remaining = total_to_process - count
        if (
            estimation_mode == TimeEstimationMode.EWMA
            and estimator is not None
            and estimator.get_estimated_time_per_asset() > 0
        ):
            ewma = estimator.get_estimated_time_per_asset()
            est_total = ewma * total_to_process
            est_remaining = ewma * remaining
        else:
            est_total = avg * total_to_process
            est_remaining = est_total - elapsed
        est_total, est_remaining = adjust_estimates(elapsed, est_total, est_remaining)
        percent_rel = (count / total_to_process) * 100
        percent_abs = None
        abs_count = count
        abs_total = total_to_process
        if skip_n is not None and total_assets is not None:
            abs_count = count + skip_n
            abs_total = total_assets
            percent_abs = (abs_count / abs_total) * 100 if abs_total else None

        def fmt_time(minutes: float) -> str:
            if minutes >= 60:
                return f"{minutes/60:.1f} h"
            else:
                return f"{minutes:.1f} min"

        msg = f"{count}/{total_to_process} ({percent_rel:.1f}% relative"
        if percent_abs is not None:
            msg += f", {abs_count}/{abs_total} ({percent_abs:.1f}% absolute)"
        msg += f") processed. Avg: {avg:.3f} s. Elapsed: {fmt_time(elapsed/60)}. Est. remaining: {fmt_time(est_remaining/60)}/{fmt_time(est_total/60)}"
        return msg
    else:
        return f"Processed {count} elements. Avg per element: {avg:.3f} s. Elapsed: {elapsed:.1f} s"


@typechecked
def print_perf(
    count: int,
    elapsed: float,
    total_to_process: Optional[int] = None,
    estimator: Optional[AdaptiveTimeEstimator] = None,
    skip_n: Optional[int] = None,
    total_assets: Optional[int] = None,
    estimation_mode: TimeEstimationMode = TimeEstimationMode.LINEAR,
) -> None:
    """
    Print performance statistics for asset processing.
    Args:
        count (int): Number of assets processed.
        elapsed (float): Elapsed time in seconds.
        total_assets (int, optional): Total number of assets to process.
    """
    print(
        "[PERF] "
        + format_perf_progress(
            count=count,
            elapsed=elapsed,
            total_to_process=total_to_process,
            estimator=estimator,
            skip_n=skip_n,
            total_assets=total_assets,
            estimation_mode=estimation_mode,
        )
    )
