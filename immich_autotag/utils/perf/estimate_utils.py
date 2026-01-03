from typing import Optional

from typeguard import typechecked


@typechecked
def adjust_estimates(
    elapsed: float,
    est_total: Optional[float],
    est_remaining: Optional[float],
) -> tuple[float, float]:
    """
    Ensure that estimated total time is never less than real elapsed time.
    Adjusts est_total and est_remaining accordingly.
    """
    if est_total is not None and est_total < elapsed:
        est_total = elapsed
        est_remaining = 0.0
    elif est_remaining is not None and est_remaining < 0:
        est_remaining = 0.0
    return est_total, est_remaining
