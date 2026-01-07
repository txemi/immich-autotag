from typing import Optional

import attrs
import pandas as pd
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AdaptiveTimeEstimator:
    """
    Estimates remaining time using an exponential weighted moving average (EWMA) over asset times.
    """

    alpha: float = 0.2
    times: list[float] = attrs.field(factory=list)
    ewma: Optional[float] = None

    @typechecked
    def update(self, time_per_asset: float) -> float:
        self.times.append(time_per_asset)
        s = pd.Series(self.times)
        self.ewma = s.ewm(alpha=self.alpha, adjust=False).mean().iloc[-1]
        return self.ewma

    @typechecked
    def get_estimated_time_per_asset(self) -> float:
        return self.ewma if self.ewma is not None else 0.0
