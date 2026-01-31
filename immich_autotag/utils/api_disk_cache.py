import json
from enum import Enum
from pathlib import Path
from typing import Optional

import attrs

from immich_autotag.config import internal_config
from immich_autotag.run_output.manager import RunOutputManager

# Global config to enable/disable caching (can be overridden by parameter)


class ApiCacheKey(Enum):
    ALBUMS = "albums"
    ASSETS = "assets"
    USERS = "users"
    ALBUM_PAGES = "album_pages"  # For caching paginated album results
    # Add more as needed


@attrs.define(auto_attribs=True, kw_only=True, slots=True)

class ApiCacheManager:
    cache_type: ApiCacheKey = attrs.field(validator=attrs.validators.instance_of(ApiCacheKey))  # Now public
    use_cache: Optional[bool] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(bool)))
    _use_cache: bool = attrs.field(init=False, validator=attrs.validators.instance_of(bool))
    _cache_subdir: str = attrs.field(default="api_cache", init=False, validator=attrs.validators.instance_of(str))

    def __attrs_post_init__(self):
        self._set_use_cache()

    def _set_use_cache(self):
        # Set _use_cache from internal_config per cache_type, unless overridden
        if self.use_cache is not None:
            self._use_cache = self.use_cache
        elif self.cache_type.value == ApiCacheKey.ASSETS.value:
            self._use_cache = internal_config.USE_CACHE_ASSETS
        elif self.cache_type.value == ApiCacheKey.ALBUMS.value:
            self._use_cache = internal_config.USE_CACHE_ALBUMS
        elif self.cache_type.value == ApiCacheKey.ALBUM_PAGES.value:
            self._use_cache = internal_config.USE_CACHE_ALBUM_PAGES
        elif self.cache_type.value == ApiCacheKey.USERS.value:
            self._use_cache = internal_config.USE_CACHE_USERS
        else:
            self._use_cache = True

    @staticmethod
    def create(
        cache_type: "ApiCacheKey", use_cache: Optional[bool] = None
    ) -> "ApiCacheManager":
        """
        Static constructor for ApiCacheManager to avoid linter/type checker issues with private attribute names.
        Use this instead of direct instantiation.
        """
        # Use 'cache_type' (not '_cache_type') to avoid linter/type checker warnings with attrs auto_attribs
        return ApiCacheManager(
            cache_type=cache_type,
            use_cache=use_cache,
        )

    def _get_cache_dir(self) -> Path:
        """
        Gets the cache directory of the current execution for the cache type.
        """
        run_execution = RunOutputManager.current().get_run_output_dir()
        return run_execution.get_api_cache_dir(self.cache_type.value)

    def save(self, key: str, data: dict[str, object] | list[dict[str, object]]) -> None:
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, key: str) -> Optional[dict[str, object] | list[dict[str, object]]]:
        if not self._use_cache:
            return None
        cache_dir = self._get_cache_dir()
        path = cache_dir / f"{key}.json"
        if path.exists() and path.stat().st_size > 0:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        for run_execution in RunOutputManager.current().find_recent_run_dirs(
            exclude_current=True
        ):
            prev_cache_dir = run_execution.get_api_cache_dir(self.cache_type.value)
            prev_path = prev_cache_dir / f"{key}.json"
            if prev_path.exists() and prev_path.stat().st_size > 0:
                with open(prev_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.save(key, data)
                return data
        return None
