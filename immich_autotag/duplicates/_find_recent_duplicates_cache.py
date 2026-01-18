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
    from immich_autotag.logging.utils import log
    from immich_autotag.logging.levels import LogLevel
    candidate_caches: list[tuple[datetime, Path]] = []
    checked_dirs = []
    if logs_dir.exists() and logs_dir.is_dir():
        for subdir in logs_dir.iterdir():
            if subdir.is_dir() and "PID" in subdir.name:
                checked_dirs.append(str(subdir))
                cache_file = subdir / "duplicates_cache.pkl"
                if cache_file.exists():
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    candidate_caches.append((mtime, cache_file))
    log(f"[DUPLICATES CACHE] Checked directories for cache: {checked_dirs}", level=LogLevel.PROGRESS)
    if candidate_caches:
        log(f"[DUPLICATES CACHE] Found candidate caches: {[{'path': str(p), 'mtime': m.strftime('%Y-%m-%d %H:%M:%S')} for m, p in candidate_caches]}", level=LogLevel.PROGRESS)
    else:
        log(f"[DUPLICATES CACHE] No candidate duplicates_cache.pkl files found in checked directories.", level=LogLevel.PROGRESS)
    candidate_caches.sort(reverse=True)
    now = datetime.now()
    for mtime, cache_file in candidate_caches:
        age_hours = (now - mtime).total_seconds() / 3600.0
        if now - mtime < timedelta(hours=max_age_hours):
            log(f"[DUPLICATES CACHE] Using cache {cache_file} (age: {age_hours:.2f}h, threshold: {max_age_hours}h)", level=LogLevel.PROGRESS)
            return cache_file
        else:
            log(f"[DUPLICATES CACHE] Skipped cache {cache_file} (too old: {age_hours:.2f}h, threshold: {max_age_hours}h)", level=LogLevel.PROGRESS)
    log(f"[DUPLICATES CACHE] No valid recent duplicates cache found (max_age_hours={max_age_hours}).", level=LogLevel.PROGRESS)
    return None
