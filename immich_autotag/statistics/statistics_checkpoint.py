"""
statistics_checkpoint.py

Utility to obtain the counter of the previous execution (skip_n) from run_statistics.yaml in the previous logs directory.
"""

from pathlib import Path
from typing import Optional

from typeguard import typechecked

from immich_autotag.config._internal_types import ErrorHandlingMode
from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
from immich_autotag.statistics.constants import RUN_STATISTICS_FILENAME
from immich_autotag.statistics.run_statistics import RunStatistics
from immich_autotag.utils.run_output_dir import (
    LOGS_LOCAL_DIR,
    find_recent_run_dirs,
    get_previous_run_output_dir,
)


@typechecked
def _find_recent_max_count(overlap: int, hours: int) -> Optional[int]:
    """
    Searches for the maximum count of runs in the last hours.
    Returns the calculated skip_n or None if there is no data.
    """
    max_count = 0
    found = False
    for d in find_recent_run_dirs(LOGS_LOCAL_DIR, max_age_hours=hours):
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
    Reads the count from a run_statistics.yaml file and calculates skip_n.
    Returns None if it does not exist or if there is an error.
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
def get_previous_skip_n(
    overlap: int = 100, use_recent_max: bool = False, hours: int = 3
) -> Optional[int]:
    """
    Searches for the counter of the previous execution (skip_n) from run_statistics.yaml.
    If use_recent_max is True, searches for the maximum of the last hours.
    Returns None if there is no data.
    """
    # If we are in DEVELOPMENT mode, force use of recent maximum and extend threshold to 48h
    if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
        use_recent_max = True
        hours = 48

    if use_recent_max:
        result = _find_recent_max_count(overlap, hours)
        if result is not None:
            return result
        # If there is no data, proceed with default mode

    prev_dir = get_previous_run_output_dir()
    if prev_dir is None:
        return None
    stats_path = prev_dir / RUN_STATISTICS_FILENAME
    return _get_count_from_stats_path(stats_path, overlap)
