from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from typeguard import typechecked

from immich_autotag.run_output.manager import RunOutputManager
from immich_autotag.statistics.run_statistics import RunStatistics





@typechecked
def get_max_skip_n_from_recent(
    logs_dir: Optional[Path] = None, max_age_hours: int = 3, overlap: int = 100
) -> Optional[int]:
    """
    Searches all run_statistics.yaml from the last max_age_hours hours and returns the maximum count minus overlap.
    """
    max_count = 0
    for run_exec in RunOutputManager.find_recent_run_dirs(logs_dir=None, max_age_hours=max_age_hours):
        stats_path = run_exec.get_run_statistics_path()
        if stats_path.exists():
            try:
                stats = RunStatistics.from_yaml(stats_path)
                count = stats.count
                if count > max_count:
                    max_count = count
            except Exception as e:
                import warnings
                warnings.warn(f"Could not load {stats_path}: {e}")
    if max_count > 0:
        return max(0, max_count - overlap)
    return None
