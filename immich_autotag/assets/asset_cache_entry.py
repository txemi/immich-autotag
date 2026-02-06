from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import attrs

from immich_autotag.api.logging_proxy.types import AssetResponseDto
from immich_autotag.assets.asset_dto_state import AssetDtoState, AssetDtoType
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.types.uuid_wrappers import AssetUUID, DuplicateUUID
from immich_autotag.utils.api_disk_cache import ApiCacheKey, ApiCacheManager

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

ASSET_CACHE_KEY = "assets"


class StaleAssetCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""

    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetCacheEntry:
    """
    Encapsulates the cached state of an asset, with freshness and reload logic.
    Attributes are private; access only via public methods.
    """

    _state: AssetDtoState = attrs.field(
        init=False, validator=attrs.validators.instance_of(AssetDtoState)
    )
    _max_age_seconds: int = attrs.field(
        init=False,
        validator=attrs.validators.instance_of(int),
        default=DEFAULT_CACHE_MAX_AGE_SECONDS,
        repr=False,
    )

    def is_stale(self) -> bool:
        loaded_at = self._state.get_loaded_at()
        age = (datetime.datetime.now() - loaded_at).total_seconds()
        return age > self._max_age_seconds

    def _reload_from_api(self, context: "ImmichContext") -> "AssetCacheEntry":
        """
        Reloads the asset state from the API and updates the cache entry. Returns self for convenience.
        """

        asset_id = self._state.get_uuid()  # Already AssetUUID
        refreshed_entry = AssetCacheEntry._from_api_entry(asset_id, context)
        self._state = refreshed_entry.get_state()
        return self

    def _ensure_fresh(self, context: "ImmichContext") -> "AssetCacheEntry":
        """
        Ensures the cache entry is fresh. If stale, reloads from API and updates self.
        Always returns self for convenience. Intended for internal use only.
        """
        if self.is_stale():
            self._reload_from_api(context)
        return self

    def _get_fresh_state(self) -> AssetDtoState:
        # Private: ensures freshness before returning the internal state
        self._ensure_fresh(ImmichContext.get_default_instance())
        return self._state

    def get_loaded_at(self) -> datetime.datetime:
        # Use the private _get_fresh_state to ensure freshness
        return self._get_fresh_state().get_loaded_at()

    @classmethod
    def _from_state(
        cls,
        *,
        state: AssetDtoState,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry from an existing state (private).
        """
        self = cls()
        self._state = state
        self._max_age_seconds = max_age_seconds
        return self

    @classmethod
    def from_cache_or_api(
        cls,
        asset_id: AssetUUID,
        *,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
        use_cache: bool = True,
    ) -> "AssetCacheEntry":
        """
        Attempts to load the asset from disk cache; if not present or corrupted, reloads from the API and saves to cache.
        asset_id must be an AssetUUID (not a plain UUID).
        """

        from immich_autotag.api.logging_proxy.assets.get_asset_info import (
            proxy_get_asset_info,
        )
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        cache_mgr = ApiCacheManager.create(cache_type=ApiCacheKey.ASSETS)
        cache_data = cache_mgr.load(str(asset_id))
        if cache_data is not None:
            # Defensive: handle both dict and list[dict] for legacy cache
            if isinstance(cache_data, dict):
                state = AssetDtoState.from_cache_dict(cache_data)
            elif cache_data:
                state = AssetDtoState.from_cache_dict(cache_data[0])
            else:
                state = None
            if state is not None:
                entry = cls._from_state(state=state, max_age_seconds=max_age_seconds)
                if not entry.is_stale():
                    return entry
        # If the cache is expired or does not exist, reload from API
        # If not in cache or corrupted, reload from API
        client = ImmichClientWrapper.get_default_instance().get_client()
        # Only convert to UUID when calling external Immich API
        dto = proxy_get_asset_info(asset_id, client, use_cache=False)
        if dto is None:
            raise RuntimeError(
                f"proxy_get_asset_info returned None for asset id={asset_id}"
            )
        state = AssetDtoState.from_dto(dto, AssetDtoType.FULL)
        cache_mgr.save(str(asset_id), state.to_cache_dict())
        return cls._from_state(state=state, max_age_seconds=max_age_seconds)

    @classmethod
    def from_cache_dict(
        cls,
        cache_data: dict[str, object] | None,
        *,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry | None":
        """
        Create an AssetCacheEntry from a cache dict, or None if not valid.
        """
        if cache_data is not None:
            # Defensive: handle both dict and list[dict] for legacy cache
            if cache_data:
                # If it's a list, use the first element
                if isinstance(cache_data, list):
                    # Defensive: only use if first element is a dict
                    from typing import cast

                    first = None
                    try:
                        # Use next(iter(...)) to avoid type checker complaints
                        first = next(iter(cache_data))
                    except Exception:
                        first = None
                    if isinstance(first, dict):
                        state = AssetDtoState.from_cache_dict(
                            cast(dict[str, object], first)
                        )
                    else:
                        state = None
                elif isinstance(cache_data, dict):  # type: ignore[redundant-expr]
                    state = AssetDtoState.from_cache_dict(cache_data)
                else:
                    state = None
            else:
                state = None
            if state is not None:
                entry = cls._from_state(state=state, max_age_seconds=max_age_seconds)
                if not entry.is_stale():
                    return entry
        return None

    @classmethod
    def from_dto_and_cache(
        cls,
        *,
        asset_id: AssetUUID,
        dto: AssetResponseDto,
        cache_mgr: ApiCacheManager,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Create an AssetCacheEntry from a DTO and save to cache.
        """
        state = AssetDtoState.from_dto(dto, AssetDtoType.FULL)
        cache_mgr.save(str(asset_id), state.to_cache_dict())
        return cls._from_state(state=state, max_age_seconds=max_age_seconds)

    # Removed methods to_cache_dict and from_cache_dict: the cache only serializes AssetDtoState

    def ensure_full_asset_loaded(self, context: "ImmichContext") -> AssetDtoState:
        """
        Ensures the asset is fully loaded with tags. If not, fetches from API and updates the cache entry.

        Uses the robust are_tags_loaded() method which validates:
        1. Tags are not Unset
        2. We're in FULL mode
        3. Both validation methods agree
        """
        state = self._get_fresh_state()

        # Use the robust validation method
        if state.are_tags_loaded():
            return state

        # Tags not loaded, need to reload from API
        self._reload_from_api(context)
        return self._state

    @classmethod
    def _from_dto_entry(
        cls,
        *,
        dto: AssetResponseDto,
        dto_type: AssetDtoType,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry from a DTO and type.
        """
        from immich_autotag.assets.asset_dto_state import AssetDtoState

        state = AssetDtoState.from_dto(dto, dto_type)
        self = cls()
        self._state = state
        self._max_age_seconds = max_age_seconds
        return self

    @classmethod
    def _from_api_entry(
        cls,
        asset_id: AssetUUID,
        context: "ImmichContext",
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Creates an AssetCacheEntry by loading the asset from the API (always FULL).
        """
        from immich_autotag.api.logging_proxy.assets.get_asset_info import (
            proxy_get_asset_info,
        )
        from immich_autotag.assets.asset_dto_state import AssetDtoType

        client_wrapper = context.get_client_wrapper()
        dto = proxy_get_asset_info(asset_id, client_wrapper.get_client())
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

    def get_uuid(self) -> AssetUUID:
        """
        Returns the UUID of the asset as a plain UUID (not AssetUUID).
        """
        return self._state.get_uuid()

    def get_original_file_name(self) -> Path:
        """
        Returns the original file name of the asset. This value is immutable, so no freshness check is needed.
        """
        return self._get_fresh_state().get_original_file_name()

    def get_tags(self) -> list["TagWrapper"]:
        """
        Returns the tags associated with this asset as TagWrapper objects, using the tag collection for central management.
        """
        state = self._get_fresh_state()
        # Use the AssetDtoState logic to get TagWrapper objects via the tag collection

        return state.get_tags()

    def get_state(self) -> AssetDtoState:
        """
        Returns the internal AssetDtoState (for compatibility with wrappers).
        """
        return self._get_fresh_state()

    def get_dates(self) -> list[datetime.datetime]:
        """
        Returns a list of date fields (created_at, file_created_at, exif_created_at) if available.
        """

        return self._state.get_dates()

    def get_is_favorite(self) -> bool:
        """
        Returns True if the asset is marked as favorite, False otherwise.
        Defensive: always returns a bool, never None.
        """
        value = self._state.get_is_favorite()
        return value

    def get_created_at(self) -> datetime.datetime:
        """
        Returns the created_at date of the asset, if available.
        """
        return self._state.get_created_at()

    def get_original_path(self) -> Path:
        """
        Returns the original file path of the asset, if available.
        """
        return self._state.get_original_path()

    def get_duplicate_id_as_uuid(self) -> DuplicateUUID | None:
        """
        Returns the duplicate id as DuplicateUUID, or None if not part of a duplicate group.

        Automatically ensures the asset is fully loaded if duplicate_id is not yet available.
        This provides transparent access to duplicate_id regardless of how the asset was initially loaded.

        Returns:
            DuplicateUUID if the asset is part of a duplicate group
            None if the asset is not part of any duplicate group
        """
        from immich_autotag.assets.asset_dto_state import DuplicateIdNotLoadedError
        from immich_autotag.context.immich_context import ImmichContext

        try:
            return self._state.get_duplicate_id_as_uuid()
        except DuplicateIdNotLoadedError:
            # duplicate_id not loaded, need to reload from API with full details
            context = ImmichContext.get_default_instance()
            self.ensure_full_asset_loaded(context)
            return self._state.get_duplicate_id_as_uuid()

    def has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the asset has a tag with the given name.
        """
        self._ensure_fresh(ImmichContext.get_default_instance())
        return self._state.has_tag(tag_name)

    @classmethod
    def from_dto_entry(
        cls,
        *,
        dto: AssetResponseDto,
        dto_type: AssetDtoType,
        max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS,
    ) -> "AssetCacheEntry":
        """
        Public wrapper for _from_dto_entry to avoid protected-access warning.
        """
        return cls._from_dto_entry(
            dto=dto, dto_type=dto_type, max_age_seconds=max_age_seconds
        )
