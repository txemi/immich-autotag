import attrs
from typeguard import typechecked
from typing import Optional
import pandas as pd



@attrs.define(auto_attribs=True, slots=True)
class AdaptiveTimeEstimator:
    """
    Estima el tiempo restante usando una media móvil exponencial (EWMA) sobre los tiempos por asset.
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
