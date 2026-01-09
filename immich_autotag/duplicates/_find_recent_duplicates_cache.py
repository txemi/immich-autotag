from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from typeguard import typechecked


@typechecked
def find_recent_duplicates_cache(logs_dir: Path, max_age_hours: int) -> Optional[Path]:
    """
    Searches for the most recent and valid duplicates_cache.pkl file in all log subfolders.
    Returns the Path if it exists and is within the freshness threshold, or None.
    """
    candidate_caches: list[tuple[datetime, Path]] = []
    if logs_dir.exists() and logs_dir.is_dir():
        for subdir in logs_dir.iterdir():
            if subdir.is_dir() and "PID" in subdir.name:
                cache_file = subdir / "duplicates_cache.pkl"
                if cache_file.exists():
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    candidate_caches.append((mtime, cache_file))
    candidate_caches.sort(reverse=True)
    now = datetime.now()
    for mtime, cache_file in candidate_caches:
        if now - mtime < timedelta(hours=max_age_hours):
            return cache_file
    return None
