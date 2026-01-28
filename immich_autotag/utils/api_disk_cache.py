
import json
from pathlib import Path
from typing import Optional
from enum import Enum
# Global config to enable/disable caching (can be overridden by parameter)
class ApiCacheKey(Enum):
    ALBUMS = "albums"
    ASSETS = "assets"
    USERS = "users"
    # Add more as needed

from immich_autotag.run_output.run_output_dir import (
    find_recent_run_dirs,
    get_run_output_dir,
)

# Global config to enable/disable caching (can be overridden by parameter)
API_CACHE_ENABLED = True

CACHE_SUBDIR = "api_cache"


def _get_cache_dir(entity: ApiCacheKey, run_dir: Optional[Path] = None) -> Path:
    """Returns the cache directory for an entity (albums, assets, etc) in the given
    run."""
    if run_dir is None:
        run_dir = get_run_output_dir()
    cache_dir = run_dir / CACHE_SUBDIR / entity.value
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def save_entity_to_cache(*, entity: ApiCacheKey, key: str, data: dict[str, object]) -> None:
    """Saves an object in the cache of the current run."""
    cache_dir = _get_cache_dir(entity)
    path = cache_dir / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_entity_from_cache(entity:
    ApiCacheKey, key: str, use_cache: Optional[bool] = None
) -> Optional[dict[str, object]]:
    """
    Searches for an object in the cache (first in the current run, then in previous
    runs). If use_cache is False, never searches in cache.
    """
    if use_cache is None:
        use_cache = API_CACHE_ENABLED
    if not use_cache:
        return None
    # 1. Search in the current run
    cache_dir = _get_cache_dir(entity)
    path = cache_dir / f"{key}.json"
    if path.exists() and path.stat().st_size > 0:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 2. Search in previous runs (ordered from most recent to oldest)
    logs_dir = Path("logs_local")
    for run_dir in find_recent_run_dirs(logs_dir, exclude_current=True):
        prev_cache_dir = run_dir / CACHE_SUBDIR / entity.value
        prev_path = prev_cache_dir / f"{key}.json"
        if prev_path.exists() and prev_path.stat().st_size > 0:
            with open(prev_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Optional: copy to the current cache to speed up future searches
            save_entity_to_cache(entity=entity, key=key, data=data)
            return data
    return None
