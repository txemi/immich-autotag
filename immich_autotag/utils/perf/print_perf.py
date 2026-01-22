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
        est_total_rel, est_remaining_rel = adjust_estimates(elapsed, est_total_rel, est_remaining_rel)
        percent_rel = (count / total_to_process) * 100

        # Absoluto (incluyendo skip_n)
        percent_abs = None
        abs_count = count
        abs_total = total_to_process
        est_total_abs = None
        est_remaining_abs = None
        if skip_n is not None and total_assets is not None and total_assets > 0:
            abs_count = count + skip_n
            abs_total = total_assets
            percent_abs = (abs_count / abs_total) * 100
            # Estimación absoluta: extrapolamos el tiempo medio a todo el total
            est_total_abs = avg * abs_total
            est_remaining_abs = est_total_abs - elapsed
            est_total_abs, est_remaining_abs = adjust_estimates(elapsed, est_total_abs, est_remaining_abs)

        def fmt_time(minutes: float) -> str:
            if minutes >= 60:
                return f"{minutes/60:.1f} h"
            else:
                return f"{minutes:.1f} min"

        msg = f"{count}/{total_to_process} ({percent_rel:.1f}% relativo"
        if percent_abs is not None:
            msg += f", {abs_count}/{abs_total} ({percent_abs:.1f}% absoluto)"
        msg += f") procesados. Avg: {avg:.3f} s. Elapsed: {fmt_time(elapsed/60)}. "
        msg += f"Est. restante (relativo): {fmt_time(est_remaining_rel/60)}/{fmt_time(est_total_rel/60)}"
        if percent_abs is not None and est_remaining_abs is not None and est_total_abs is not None:
            msg += f" | Est. restante (absoluto): {fmt_time(est_remaining_abs/60)}/{fmt_time(est_total_abs/60)}"
        return msg
    else:
        return (
            f"Processed {count} elements. Avg per element: {avg:.3f} s. "
            f"Elapsed: {elapsed:.1f} s"
        )


