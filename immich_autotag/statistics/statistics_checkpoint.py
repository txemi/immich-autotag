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
def get_previous_skip_n(overlap: int = 100) -> Optional[int]:
    """
    Looks for the previous run's run_statistics.yaml and returns the count minus the overlap.
    Returns None if not found.
    Now loads the statistics using the RunStatistics class for better validation.
    """
    prev_dir = get_previous_run_output_dir()
    if prev_dir is None:
        return None
    stats_path = prev_dir / RUN_STATISTICS_FILENAME
    if not stats_path.exists():
        return None
    try:
        stats = RunStatistics.from_yaml(stats_path)
    except Exception as e:
        # Optionally log or print the error
        return None
    count = stats.count
    skip_n = max(0, count - overlap)
    return skip_n
