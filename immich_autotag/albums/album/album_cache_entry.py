from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import attrs

from immich_autotag.albums.album.album_dto_state import AlbumDtoState
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID, UserUUID
from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:
    from immich_client.models.album_response_dto import AlbumResponseDto

    from immich_autotag.albums.album.album_dto_state import AlbumLoadSource
    from immich_autotag.albums.album.album_user_list import AlbumUserList
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.context.immich_context import ImmichContext


class StaleAlbumCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""


@attrs.define(auto_attribs=True, slots=True)
class AlbumCacheEntry:

    _dto: AlbumDtoState
    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS
    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)

    def merge_from_dto(
        self, dto: "AlbumResponseDto", load_source: "AlbumLoadSource"
    ) -> None:
        """
        Delegates to AlbumDtoState.merge_from_dto. See AlbumDtoState for logic.
        """
        self._dto.merge_from_dto(dto, load_source)

    def get_start_date(self) -> datetime.datetime | None:
        return self._dto.get_start_date()

    def get_end_date(self) -> datetime.datetime | None:
        return self._dto.get_end_date()

    def get_owner_uuid(self) -> "UserUUID":
        return self._dto.get_owner_uuid()

    def get_album_users(self) -> "AlbumUserList":
        return self._dto.get_album_users()

    def update(
        self, *, dto: "AlbumResponseDto", load_source: "AlbumLoadSource"
    ) -> None:
        self._dto.update(dto=dto, load_source=load_source)

    def is_full(self) -> bool:
        return self._dto.is_full()

    @classmethod
    def _from_cache_or_api(
        cls,
        album_id: AlbumUUID,
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> AlbumDtoState:
        """
        Attempts to load the album from cache. If it is stale or does not exist, fetches from API.
        Returns an AlbumDtoState directly.
        """
        album_id_str = str(album_id)
        from immich_autotag.utils.api_disk_cache import ApiCacheKey, ApiCacheManager

        cache_mgr = ApiCacheManager.create(cache_type=ApiCacheKey.ALBUMS)
        cache_data = cache_mgr.load(album_id_str)
        from immich_client.models.album_response_dto import AlbumResponseDto

        from immich_autotag.albums.album.album_dto_state import AlbumLoadSource

        if isinstance(cache_data, dict):
            cached_album_dto = AlbumResponseDto.from_dict(cache_data)
            dto = AlbumDtoState.create(
                dto=cached_album_dto, load_source=AlbumLoadSource.DETAIL
            )
            # Use public is_stale method
            if not dto.is_stale():
                return dto

        # API fetch logic: call proxy_get_album_info using the default Immich client
        from immich_autotag.api.immich_proxy.albums import proxy_get_album_info
        from immich_autotag.context.immich_context import ImmichContext

        client = ImmichContext.get_default_instance().get_client_wrapper().get_client()
        album_dto = proxy_get_album_info(
            album_id=album_id, client=client, use_cache=False
        )
        if album_dto is None:
            from immich_autotag.utils.url_helpers import get_immich_album_url

            album_url = get_immich_album_url(album_id).geturl()
            raise RuntimeError(
                f"Could not fetch album info for album_id={album_id} (link: {album_url})"
            )
        # Explicit assert for mypy type narrowing
        assert album_dto is not None
        from immich_autotag.utils.api_disk_cache import ApiCacheKey

        cache_mgr.save(album_id_str, album_dto.to_dict())
        return AlbumDtoState.create(dto=album_dto, load_source=AlbumLoadSource.DETAIL)

    def is_stale(self) -> bool:
        return self._dto.is_stale()

    def get_state(self) -> AlbumDtoState:
        if self.is_stale():
            raise StaleAlbumCacheError(
                f"Album cache entry is stale (>{self._max_age_seconds}s)"
            )
        return self._dto

    def _ensure_full_loaded(self) -> "AlbumCacheEntry":
        """
        Ensures the DTO is of type DETAIL (full). If not, reloads using _from_cache_or_api.
        If already full, does nothing. If not full and no reload_func is provided, raises exception.
        PRIVATE: Only AlbumCacheEntry should decide when to reload.
        """
        if self._dto.is_full():
            return self
        # Reload the DTO using the new DTO returned by _from_cache_or_api
        new_dto: AlbumDtoState = self._from_cache_or_api(
            album_id=self._dto.get_album_id(),
            max_age_seconds=self._max_age_seconds,
            use_cache=False,
        )
        # Use only public API: update with the new AlbumResponseDto and load_source
        self._dto.update(
            dto=new_dto.get_dto(),
            load_source=new_dto.get_load_source(),
        )
        return self

    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Does not force reload, uses the current DTO.
        """
        return self._ensure_full_loaded()._dto.is_empty()

    # Removed unused _get_dto method (was exposing internal state)

    def get_asset_uuids(self) -> set[AssetUUID]:
        """
        Returns the set of asset UUIDs in the album, ensuring full DTO is loaded.
        Does not expose DTOs directly.
        """
        return self._ensure_full_loaded()._dto.get_asset_uuids()

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        # Import here to avoid circular imports

        return asset_wrapper.get_id() in self._ensure_full_loaded().get_asset_uuids()

    @conditional_typechecked
    def get_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        # Ensure the album is fully loaded before accessing assets
        self._ensure_full_loaded()
        from immich_autotag.assets.asset_dto_state import AssetDtoType

        asset_manager = context.get_asset_manager()
        # asset_manager should not be None; if it is, this is a programming error
        result: list["AssetResponseWrapper"] = []
        for a in self._ensure_full_loaded()._dto.get_assets():
            b = asset_manager.get_wrapper_for_asset_dto(
                asset_dto=a,
                dto_type=AssetDtoType.ALBUM,
                context=context,
            )
            result.append(b)
        return result

    def get_album_id(self) -> AlbumUUID:
        """
        Returns the album UUID by delegating to the DTO state.
        """
        return self._dto.get_album_id()

    def get_album_name(self) -> str:
        """
        Returns the album name by delegating to the DTO state.
        """
        return self._dto.get_album_name()

    @staticmethod
    def create(
        dto: AlbumDtoState, max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS
    ) -> "AlbumCacheEntry":
        """
        Static constructor for AlbumCacheEntry to avoid linter/type checker issues with private attribute names.
        Use this instead of direct instantiation.
        This pattern uses a single-argument constructor for attrs compatibility, then sets additional fields via a private setter.
        See docs/dev/style.md for details.
        """
        entry = AlbumCacheEntry(dto)
        entry._set_max_age_seconds(max_age_seconds)
        return entry

    def _set_max_age_seconds(self, value: int) -> None:
        """Private setter for _max_age_seconds to support single-argument construction pattern."""
        self._max_age_seconds = value
