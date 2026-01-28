from immich_autotag.run_output.run_output_dir import get_run_output_dir, find_recent_run_dirs
import json
from enum import Enum
from pathlib import Path
from typing import Optional


# Global config to enable/disable caching (can be overridden by parameter)

class ApiCacheKey(Enum):
    ALBUMS = "albums"
    ASSETS = "assets"
    USERS = "users"
    ALBUM_PAGES = "album_pages"  # For caching paginated album results
    # Add more as needed



import attrs

@attrs.define(auto_attribs=True, slots=True)
class ApiCacheManager:
    cache_type: ApiCacheKey
    use_cache: bool = True
    cache_subdir: str = "api_cache"

    def _get_cache_dir(self, run_dir: Optional[Path] = None) -> Path:
        if run_dir is None:
            run_dir = get_run_output_dir()
        cache_dir = run_dir / self.cache_subdir / self.cache_type.value
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def save(self, key: str, data: dict[str, object]) -> None:
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, key: str) -> Optional[dict[str, object]]:
        if not self.use_cache:
            return None
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        if path.exists() and path.stat().st_size > 0:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        logs_dir = Path("logs_local")
        for run_dir in find_recent_run_dirs(logs_dir, exclude_current=True):
            prev_cache_dir = run_dir / self.cache_subdir / self.cache_type.value
            prev_path = prev_cache_dir / f"{key}.json"
            if prev_path.exists() and prev_path.stat().st_size > 0:
                with open(prev_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.save(key, data)
                return data
        return None

