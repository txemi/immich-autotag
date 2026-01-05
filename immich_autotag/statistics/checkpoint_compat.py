"""
Legacy checkpoint compatibility layer for migration to statistics system.
Redirects checkpoint calls to the new statistics manager.
"""

from typeguard import typechecked

from immich_autotag.statistics.statistics_manager import (RunStatistics,
                                                          StatisticsManager)

_stats_manager = StatisticsManager()


@typechecked
def load_checkpoint() -> tuple[str | None, int]:
    stats = _stats_manager.load_latest()
    if stats:
        return stats.last_processed_id, stats.count
    return None, 0


@typechecked
def save_checkpoint(asset_id: str, count: int) -> None:
    # Usar el método update del singleton para actualizar y guardar el estado
    _stats_manager.update(last_processed_id=asset_id, count=count)


@typechecked
def delete_checkpoint() -> None:
    _stats_manager.delete_all()
