from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from typeguard import typechecked


from immich_autotag.utils.run_output_dir import find_recent_run_dirs

@typechecked
def find_recent_duplicates_cache(logs_dir: Path, max_age_hours: int) -> Optional[Path]:
    """
    Busca el archivo de caché de duplicados más reciente y válido en las subcarpetas de logs.
    Devuelve la ruta si existe y está dentro del umbral de antigüedad, o None.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from datetime import datetime

    checked_dirs = []
    candidate_caches: list[tuple[datetime, Path]] = []
    for subdir in find_recent_run_dirs(logs_dir, max_age_hours=max_age_hours):
        checked_dirs.append(str(subdir))
        cache_file = subdir / "duplicates_cache.pkl"
        if cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            candidate_caches.append((mtime, cache_file))
    log(
        f"[DUPLICATES CACHE] Checked directories for cache: {checked_dirs}",
        level=LogLevel.PROGRESS,
    )
    if candidate_caches:
        log(
            f"[DUPLICATES CACHE] Found candidate caches: {[{'path': str(p), 'mtime': m.strftime('%Y-%m-%d %H:%M:%S')} for m, p in candidate_caches]}",
            level=LogLevel.PROGRESS,
        )
    else:
        log(
            f"[DUPLICATES CACHE] No candidate duplicates_cache.pkl files found in checked directories.",
            level=LogLevel.PROGRESS,
        )
    candidate_caches.sort(reverse=True)
    now = datetime.now()
    for mtime, cache_file in candidate_caches:
        age_hours = (now - mtime).total_seconds() / 3600.0
        if now - mtime < timedelta(hours=max_age_hours):
            log(
                f"[DUPLICATES CACHE] Using cache {cache_file} (age: {age_hours:.2f}h, threshold: {max_age_hours}h)",
                level=LogLevel.PROGRESS,
            )
            return cache_file
        else:
            log(
                f"[DUPLICATES CACHE] Skipped cache {cache_file} (too old: {age_hours:.2f}h, threshold: {max_age_hours}h)",
                level=LogLevel.PROGRESS,
            )
    log(
        f"[DUPLICATES CACHE] No valid recent duplicates cache found (max_age_hours={max_age_hours}).",
        level=LogLevel.PROGRESS,
    )
    return None
