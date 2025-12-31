import uuid
from typing import Optional, Union
from urllib.parse import ParseResult, urlparse

import attrs
import pandas as pd
from typeguard import typechecked

from immich_autotag.config.internal_config import (IMMICH_PHOTO_PATH_TEMPLATE,
                                                   IMMICH_WEB_BASE_URL)


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


@typechecked
def print_perf(
    count: int,
    elapsed: float,
    total_assets: int | None = None,
    estimator: "AdaptiveTimeEstimator" = None,
):
    """
    Print performance statistics for asset processing.
    Args:
        count (int): Number of assets processed.
        elapsed (float): Elapsed time in seconds.
        total_assets (int, optional): Total number of assets to process.
    """
    avg = elapsed / count if count else 0
    if total_assets and count > 0:
        remaining = total_assets - count
        if estimator is not None and estimator.get_estimated_time_per_asset() > 0:
            ewma = estimator.get_estimated_time_per_asset()
            est_total = ewma * total_assets
            est_remaining = ewma * remaining
        else:
            est_total = avg * total_assets
            est_remaining = est_total - elapsed
        percent = (count / total_assets) * 100

        def fmt_time(minutes: float) -> str:
            if minutes >= 60:
                return f"{minutes/60:.1f} h"
            else:
                return f"{minutes:.1f} min"

        print(
            f"[PERF] {count}/{total_assets} ({percent:.1f}%) assets processed. Avg: {avg:.3f} s. Est. remaining: {fmt_time(est_remaining/60)}/{fmt_time(est_total/60)}"
        )
    else:
        print(f"[PERF] Processed {count} assets. Average per asset: {avg:.3f} s")


@typechecked
def get_immich_photo_url(asset_id: uuid.UUID) -> ParseResult:
    """
    Devuelve la URL web de Immich para un asset dado su id (UUID) como ParseResult.
    """
    if not isinstance(asset_id, uuid.UUID):
        raise TypeError(f"asset_id debe ser uuid.UUID, no {type(asset_id)}")
    asset_id_str = str(asset_id)
    url = f"{IMMICH_WEB_BASE_URL}{IMMICH_PHOTO_PATH_TEMPLATE.format(id=asset_id_str)}"
    return urlparse(url)
