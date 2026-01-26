from immich_autotag.context.immich_context import ImmichContext

ASSET_CACHE_KEY = "assets"
import datetime
from uuid import UUID

import attrs

from immich_autotag.assets.asset_dto_state import AssetDtoState, AssetDtoType
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS


class StaleAssetCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""

    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetCacheEntry:
    """
    Encapsulates the cached state of an asset, with freshness and reload logic.
    Attributes are private; access only via public methods.
    """

    _state: AssetDtoState
    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS  # Global default

    def is_stale(self) -> bool:
        age = (datetime.datetime.now() - self._state.get_loaded_at()).total_seconds()
        return age > self._max_age_seconds

    def _get_fresh_state(self) -> AssetDtoState:
        # Private: ensures freshness before returning the internal state
        self._ensure_fresh(ImmichContext.get_default_instance())
        return self._state

    def get_loaded_at(self) -> datetime.datetime:
        # Use the private _get_fresh_state to ensure freshness
        return self._get_fresh_state().get_loaded_at()

    @classmethod
    def from_cache_or_api(
        cls,
        asset_id: UUID,
        *,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
        use_cache: bool = True,
    ) -> "AssetCacheEntry":
        """
        Attempts to load the asset from disk cache; if not present or corrupted, reloads from the API and saves to cache.
        asset_id must be a UUID.
        """

        from immich_autotag.api.immich_proxy.assets import proxy_get_asset_info
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.utils.api_disk_cache import (
            get_entity_from_cache,
            save_entity_to_cache,
        )

        cache_data = get_entity_from_cache(
            ASSET_CACHE_KEY, str(asset_id), use_cache=use_cache
        )
        if cache_data is not None:
            state = AssetDtoState.from_cache_dict(cache_data)
            entry = cls(state=state, max_age_seconds=max_age_seconds)
            if not entry.is_stale():
                return entry
        # If the cache is expired or does not exist, reload from API
        # If not in cache or corrupted, reload from API
        client = ImmichClientWrapper.get_default_instance().get_client()
        dto = proxy_get_asset_info(asset_id, client, use_cache=False)
        if dto is None:
            raise RuntimeError(
                f"proxy_get_asset_info returned None for asset id={asset_id}"
            )
        state = AssetDtoState(dto=dto, api_endpoint_source=AssetDtoType.FULL)
        save_entity_to_cache(
            entity=ASSET_CACHE_KEY, key=str(asset_id), data=state.to_cache_dict()
        )
        return cls(state=state, max_age_seconds=max_age_seconds)

    @classmethod
    def _from_state(
        cls, state: AssetDtoState, max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry from an existing state (private).
        """
        return cls(state=state, max_age_seconds=max_age_seconds)

    # Removed methods to_cache_dict and from_cache_dict: the cache only serializes AssetDtoState

    def ensure_full_asset_loaded(self, context: "ImmichContext") -> AssetDtoState:
        """
        Ensures the asset is fully loaded (type FULL). If not, fetches from API and updates the cache entry.
        """
        state = self._get_fresh_state()
        from immich_autotag.assets.asset_dto_state import AssetDtoType

        if state.get_type() == AssetDtoType.FULL:
            return state

        self._reload_from_api(context)
        return self._state

    def _reload_from_api(self, context: "ImmichContext") -> "AssetCacheEntry":
        """
        Reloads the asset state from the API and updates the cache entry. Returns self for convenience.
        """
        asset_id = self._state.get_uuid()
        refreshed_entry = AssetCacheEntry._from_api_entry(asset_id, context)
        self._state = refreshed_entry._state
        return self

    @classmethod
    def _from_dto_entry(
        cls,
        *,
        dto: "AssetResponseDto",  # Use the real DTO type if available
        dto_type: AssetDtoType,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry from a DTO and type.
        """
        from immich_autotag.assets.asset_dto_state import AssetDtoState

        state = AssetDtoState(dto=dto, api_endpoint_source=dto_type)
        return cls(state=state, max_age_seconds=max_age_seconds)

    @classmethod
    def _from_api_entry(
        cls,
        asset_id: UUID,
        context: "ImmichContext",
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry by loading the asset from the API (always FULL).
        """
        from immich_autotag.api.immich_proxy.assets import (
            proxy_get_asset_info,
        )
        from immich_autotag.assets.asset_dto_state import AssetDtoType

        dto = proxy_get_asset_info(asset_id, context.get_client().get_client())
        if dto is None:
            raise RuntimeError(
                f"proxy_get_asset_info returned None for asset id={asset_id}"
            )
        return cls._from_dto_entry(
            dto=dto,
            dto_type=AssetDtoType.FULL,
            max_age_seconds=max_age_seconds,
        )

    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset, or an empty list if not available.
        """
        state = self._get_fresh_state()
        return state.get_tag_names()

    def _ensure_fresh(self, context: "ImmichContext") -> "AssetCacheEntry":
        """
        Ensures the cache entry is fresh. If stale, reloads from API and updates self.
        Always returns self for convenience. Intended for internal use only.
        """
        if self.is_stale():
            self._reload_from_api(context)
        return self

    def get_uuid(self) -> UUID:
        """
        Returns the UUID of the asset. The asset ID is immutable, so we do not require a fresh state for this operation.
        """
        return self._state.get_uuid()

    def get_original_file_name(self) -> str:
        """
        Returns the original file name of the asset. This value is immutable, so no freshness check is needed.
        """
        return self._get_fresh_state().get_original_file_name()
