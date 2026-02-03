import json
import logging
from enum import Enum
from pathlib import Path
from typing import Optional

import attrs

from immich_autotag.config import internal_config
from immich_autotag.run_output.manager import RunOutputManager

logger = logging.getLogger(__name__)

# Global config to enable/disable caching (can be overridden by parameter)


class ApiCacheKey(Enum):
    ALBUMS = "albums"
    ASSETS = "assets"
    USERS = "users"
    ALBUM_PAGES = "album_pages"  # For caching paginated album results
    # Add more as needed


@attrs.define(auto_attribs=True, slots=True)
class ApiCacheManager:
    _cache_type: ApiCacheKey = attrs.field(
        validator=attrs.validators.instance_of(ApiCacheKey)
    )
    _use_cache: bool = attrs.field(
        init=False, validator=attrs.validators.instance_of(bool)
    )
    _cache_subdir: str = attrs.field(
        default="api_cache", init=False, validator=attrs.validators.instance_of(str)
    )

    def _set_use_cache(self):
        # Set _use_cache from internal_config per cache_type
        if self._cache_type.value == ApiCacheKey.ASSETS.value:
            self._use_cache = internal_config.USE_CACHE_ASSETS
        elif self._cache_type.value == ApiCacheKey.ALBUMS.value:
            self._use_cache = internal_config.USE_CACHE_ALBUMS
        elif self._cache_type.value == ApiCacheKey.ALBUM_PAGES.value:
            self._use_cache = internal_config.USE_CACHE_ALBUM_PAGES
        elif self._cache_type.value == ApiCacheKey.USERS.value:
            self._use_cache = internal_config.USE_CACHE_USERS
        else:
            self._use_cache = True

    def __attrs_post_init__(self):
        self._set_use_cache()

    @staticmethod
    def create(cache_type: "ApiCacheKey") -> "ApiCacheManager":
        """
        Static constructor for ApiCacheManager to avoid linter/type checker issues with private attribute names.
        Use this instead of direct instantiation.
        """
        obj = ApiCacheManager(cache_type)

        return obj

    def _get_cache_dir(self) -> Path:
        """
        Gets the cache directory of the current execution for the cache type.
        """
        run_execution = RunOutputManager.current().get_run_output_dir()
        return run_execution.get_api_cache_dir(self._cache_type.value)

    def save(self, key: str, data: dict[str, object] | list[dict[str, object]]) -> None:
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data, f, ensure_ascii=False, indent=2
            )

    def _try_load_json(
        self, path: Path
    ) -> Optional[dict[str, object] | list[dict[str, object]]]:
        """Try to load JSON from a single cache file with error handling."""
        if not path.exists() or path.stat().st_size == 0:
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.warning(
                f"Corrupted cache file {path}: {e}"
            )
            # Try to delete the corrupted file
            try:
                path.unlink()
            except Exception:
                pass
            return None

    def load(self, key: str) -> Optional[dict[str, object] | list[dict[str, object]]]:
        if not self._use_cache:
            return None

        # Try current run cache
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        data = self._try_load_json(path)
        if data is not None:
            return data

        # Try previous run caches
        for run_execution in RunOutputManager.current().find_recent_run_dirs(
            exclude_current=True
        ):
            prev_cache_dir = run_execution.get_api_cache_dir(self._cache_type.value)
            prev_path = prev_cache_dir / f"{key}.json"
            data = self._try_load_json(prev_path)
            if data is not None:
                self.save(key, data)  # Cache for current run
                return data

        return None
