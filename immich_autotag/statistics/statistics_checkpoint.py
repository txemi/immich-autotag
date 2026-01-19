"""
statistics_checkpoint.py

Utility to obtain the counter of the previous execution (skip_n) from run_statistics.yaml in the previous logs directory.
"""

from pathlib import Path
from typing import Optional

from typeguard import typechecked

from immich_autotag.statistics.constants import RUN_STATISTICS_FILENAME
from immich_autotag.statistics.run_statistics import RunStatistics
from immich_autotag.utils.run_output_dir import get_previous_run_output_dir

@typechecked

@typechecked
def _find_recent_max_count(overlap: int, hours: int) -> Optional[int]:
    """
    Busca el máximo count de los runs en las últimas `hours` horas.
    Devuelve el skip_n calculado o None si no hay datos.
    """
    from datetime import datetime, timedelta
    from immich_autotag.utils.run_output_dir import LOGS_LOCAL_DIR

    now = datetime.now()
    cutoff = now - timedelta(hours=hours)
    max_count = 0
    found = False
    for d in LOGS_LOCAL_DIR.iterdir():
        if d.is_dir() and "PID" in d.name:
            try:
                dt_str = d.name.split("_PID")[0]
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
            except Exception:
                continue
            if dt < cutoff:
                continue
            stats_path = d / RUN_STATISTICS_FILENAME
            if stats_path.exists():
                try:
                    stats = RunStatistics.from_yaml(stats_path)
                    if stats.count > max_count:
                        max_count = stats.count
                        found = True
                except Exception:
                    continue
    if found:
        return max(0, max_count - overlap)
    return None

@typechecked
def _get_count_from_stats_path(stats_path: Path, overlap: int) -> Optional[int]:
    """
    Lee el count de un fichero run_statistics.yaml y calcula skip_n.
    Devuelve None si no existe o hay error.
    """
    if not stats_path.exists():
        return None
    try:
        stats = RunStatistics.from_yaml(stats_path)
    except Exception:
        return None
    count = stats.count
    return max(0, count - overlap)

@typechecked
def get_previous_skip_n(overlap: int = 100, use_recent_max: bool = False, hours: int = 3) -> Optional[int]:
    """
    Busca el contador de la ejecución anterior (skip_n) a partir de run_statistics.yaml.
    Si use_recent_max es True, busca el máximo de las últimas `hours` horas.
    Devuelve None si no hay datos.
    """
    if use_recent_max:
        result = _find_recent_max_count(overlap, hours)
        if result is not None:
            return result
        # Si no hay datos, sigue con el modo por defecto

    prev_dir = get_previous_run_output_dir()
    if prev_dir is None:
        return None
    stats_path = prev_dir / RUN_STATISTICS_FILENAME
    return _get_count_from_stats_path(stats_path, overlap)
