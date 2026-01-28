from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import attrs

from immich_autotag.albums.album.album_dto_state import AlbumDtoState
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.utils.api_disk_cache import (
    get_entity_from_cache,
    save_entity_to_cache,
)
from immich_autotag.utils.decorators import conditional_typechecked

if TYPE_CHECKING:

    pass


class StaleAlbumCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""


@attrs.define(auto_attribs=True, kw_only=True, slots=True)
class AlbumCacheEntry:

    _dto: AlbumDtoState
    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS
    _asset_ids_cache: set[str] | None = attrs.field(default=None, init=False)

    @classmethod
    def _from_cache_or_api(
        cls,
        album_id: UUID,
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> AlbumDtoState:
        """
        Attempts to load the album from cache. If it is stale or does not exist, fetches from API.
        Returns an AlbumDtoState directly.
        """
        album_id_str = str(album_id)
        from immich_autotag.utils.api_disk_cache import ApiCacheKey

        cache_data = get_entity_from_cache(
            entity=ApiCacheKey.ALBUMS, key=album_id_str, use_cache=use_cache
        )
        from immich_client.models.album_response_dto import AlbumResponseDto

        from immich_autotag.albums.album.album_dto_state import AlbumLoadSource

        if cache_data is not None:
            try:
                album_dto = AlbumResponseDto.from_dict(cache_data)
                dto = AlbumDtoState.create(
                    dto=album_dto, load_source=AlbumLoadSource.DETAIL
                )
                # Check staleness using a temp AlbumCacheEntry
                if not dto._is_stale(max_age_seconds=max_age_seconds):
                    return dto
            except Exception:
                pass  # If the cache is corrupt, reload from API
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
        from immich_autotag.utils.api_disk_cache import ApiCacheKey

        save_entity_to_cache(
            entity=ApiCacheKey.ALBUMS, key=album_id_str, data=album_dto.to_dict()
        )
        return AlbumDtoState.create(dto=album_dto, load_source=AlbumLoadSource.DETAIL)

    def is_stale(self) -> bool:
        return self._dto._is_stale()

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
        self._dto.update(dto=new_dto._dto, load_source=new_dto._load_source)
        return self

    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Does not force reload, uses the current DTO.
        """
        return self._ensure_full_loaded()._dto.is_empty()

    def _get_dto(self) -> AlbumDtoState:
        return self._dto

    def get_asset_uuids(self) -> set[UUID]:
        """
        Returns the set of asset UUIDs in the album, ensuring full DTO is loaded.
        Does not expose DTOs directly.
        """
        return self._ensure_full_loaded()._get_dto().get_asset_uuids()

    @conditional_typechecked
    def has_asset_wrapper(
        self, asset_wrapper: "AssetResponseWrapper", use_cache: bool = True
    ) -> bool:
        raise NotImplementedError("usar cache")
        return (
            asset_wrapper.get_id_as_uuid()
            in self._ensure_full_loaded().get_asset_uuids()
        )

    @conditional_typechecked
    def get_assets(self, context: "ImmichContext") -> list["AssetResponseWrapper"]:
        # Ensure the album is fully loaded before accessing assets
        self._ensure_full_loaded()
        from immich_autotag.context.immich_context import ImmichContext

        asset_manager = ImmichContext.get_default_instance().get_asset_manager()
        if asset_manager is None:
            raise AttributeError("ImmichContext missing asset_manager")
        result = []
        for a in self._dto.assets:
            b = asset_manager.get_wrapper_for_asset_dto(a, AlbumDtoType.ALBUM, context)
            result.append(b)
        return result

    def get_album_id(self) -> UUID:
        """
        Returns the album UUID by delegating to the DTO state.
        """
        return self._dto.get_album_id()

    def get_album_name(self) -> str:
        """
        Returns the album name by delegating to the DTO state.
        """
        return self._dto.get_album_name()
