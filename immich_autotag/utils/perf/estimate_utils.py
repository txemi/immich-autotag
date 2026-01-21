from typing import Optional

import attrs
from typeguard import typechecked


@attrs.define(auto_attribs=True, on_setattr=attrs.setters.validate)
class AdjustEstimatesResult:
    est_total: float = attrs.field(validator=attrs.validators.instance_of(float))
    est_remaining: float = attrs.field(validator=attrs.validators.instance_of(float))

    def __iter__(self):
        # Allow tuple-like unpacking: est_total, est_remaining = adjust_estimates(...)
        yield self.est_total
        yield self.est_remaining


@typechecked
def adjust_estimates(
    elapsed: float,
    est_total: Optional[float],
    est_remaining: Optional[float],
) -> AdjustEstimatesResult:
    """
    Ensure that estimated total time is never less than real elapsed time.
    Adjusts est_total and est_remaining accordingly.
    """
    if est_total is not None and est_total < elapsed:
        est_total = elapsed
        est_remaining = 0.0
    elif est_remaining is not None and est_remaining < 0:
        est_remaining = 0.0
    # coerce to floats
    return AdjustEstimatesResult(est_total or 0.0, est_remaining or 0.0)
