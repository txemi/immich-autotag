from pathlib import Path
from typing import Optional

from typeguard import typechecked

from immich_autotag.duplicates.duplicates_cache_constants import (
    DUPLICATES_CACHE_FILENAME,
)
from immich_autotag.duplicates.duplicates_cache_file import DuplicatesCacheFile
from immich_autotag.utils.run_output_dir import find_recent_run_dirs


@typechecked
def find_recent_duplicates_cache(logs_dir: Path, max_age_hours: int) -> Optional[Path]:
    """
    Searches for the most recent and valid duplicates cache file in the logs subfolders.
    Returns the path if it exists and is within the age threshold, or None.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    checked_dirs: list[DuplicatesCacheFile] = []
    candidate_caches: list[DuplicatesCacheFile] = []
    for subdir in find_recent_run_dirs(logs_dir, max_age_hours=max_age_hours):
        cache = DuplicatesCacheFile(directory=subdir)
        checked_dirs.append(cache)
        if cache.exists():
            candidate_caches.append(cache)

    log(
        "[DUPLICATES CACHE] Checked directories status:\n"
        + "\n".join([f" - {c.status_string()}" for c in checked_dirs]),
        level=LogLevel.PROGRESS,
    )
    if candidate_caches:
        candidate_info = [
            f"{{'path': '{str(c.path)}', 'mtime': '{c.mtime().strftime('%Y-%m-%d %H:%M:%S')}'}}"
            for c in candidate_caches
        ]
        log(
            "[DUPLICATES CACHE] Found candidate caches: " + str(candidate_info),
            level=LogLevel.PROGRESS,
        )
    else:
        log(
            f"[DUPLICATES CACHE] No candidate {DUPLICATES_CACHE_FILENAME} files found in checked directories.",
            level=LogLevel.PROGRESS,
        )
    candidate_caches.sort(key=lambda c: c.mtime(), reverse=True)
    for cache in candidate_caches:
        age_hours = cache.age_hours_from()
        if cache.is_fresh(max_age_hours):
            log(
                f"[DUPLICATES CACHE] Using cache {cache.path} (age: {age_hours:.2f}h, threshold: {max_age_hours}h)",
                level=LogLevel.PROGRESS,
            )
            return cache.path
        else:
            log(
                f"[DUPLICATES CACHE] Skipped cache {cache.path} (too old: {age_hours:.2f}h, threshold: {max_age_hours}h)",
                level=LogLevel.PROGRESS,
            )
    log(
        f"[DUPLICATES CACHE] No valid recent duplicates cache found (max_age_hours={max_age_hours}).",
        level=LogLevel.PROGRESS,
    )
    return None
