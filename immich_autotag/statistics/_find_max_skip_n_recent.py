from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from typeguard import typechecked

from immich_autotag.statistics.run_statistics import RunStatistics


@typechecked
def find_recent_statistics_dirs(logs_dir: Path, max_age_hours: int = 3) -> List[Path]:
    """
    Returns a list of log folders from the last max_age_hours hours.
    """
    now = datetime.now()
    recent_dirs: List[tuple[datetime, Path]] = []
    for subdir in logs_dir.iterdir():
        if subdir.is_dir() and "PID" in subdir.name:
            try:
                dt_str = subdir.name.split("_PID")[0]
                dt = datetime.strptime(dt_str, "%Y%m%d_%H%M%S")
                if now - dt < timedelta(hours=max_age_hours):
                    recent_dirs.append((dt, subdir))
            except Exception:
                continue
    # Sort by date descending
    recent_dirs.sort(reverse=True)
    return [d for _, d in recent_dirs]


@typechecked
def get_max_skip_n_from_recent(
    logs_dir: Path, max_age_hours: int = 3, overlap: int = 100
) -> Optional[int]:
    """
    Searches all run_statistics.yaml from the last max_age_hours hours and returns the maximum count minus overlap.
    """
    max_count = 0
    for d in find_recent_statistics_dirs(logs_dir, max_age_hours):
        stats_path = d / "run_statistics.yaml"
        if stats_path.exists():
            try:
                with open(stats_path, "r", encoding="utf-8") as f:
                    stats = RunStatistics.from_yaml(f.read())
                count = stats.count
                if count > max_count:
                    max_count = count
            except Exception as e:
                import warnings
                warnings.warn(f"Could not load {stats_path}: {e}")
    if max_count > 0:
        return max(0, max_count - overlap)
    return None
