from __future__ import annotations

import time
from typing import TYPE_CHECKING
from uuid import UUID

import attrs

from immich_autotag.albums.album.album_dto_state import AlbumDtoState
from immich_autotag.config.cache_config import DEFAULT_CACHE_MAX_AGE_SECONDS
from immich_autotag.utils.api_disk_cache import (
    get_entity_from_cache,
    save_entity_to_cache,
)

if TYPE_CHECKING:

    from immich_client.models.album_response_dto import AlbumResponseDto


class StaleAlbumCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""


@attrs.define(auto_attribs=True, kw_only=True, slots=True)
class AlbumCacheEntry:

    _dto: AlbumDtoState
    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS

    @classmethod
    def from_cache_or_api(
        cls,
        album_id: "UUID",
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> "AlbumCacheEntry":
        """
        Attempts to load the album from cache. If it is stale or does not exist, this method must be completed with an API fetch implementation.
        """
        album_id_str = str(album_id)
        cache_data = get_entity_from_cache("albums", album_id_str, use_cache=use_cache)
        if cache_data is not None:
            try:
                dto = AlbumDtoState.from_dict(cache_data)
                entry = cls(dto=dto, max_age_seconds=max_age_seconds)
                if not entry.is_stale():
                    return entry
            except Exception:
                pass  # If the cache is corrupt, reload from API
        # API fetch logic: call proxy_get_album_info using the default Immich client
        from immich_autotag.context.immich_context import ImmichContext
        from immich_autotag.api.immich_proxy.albums import proxy_get_album_info

        client = ImmichContext.get_default_instance().get_client_wrapper().get_client()
        album_dto = proxy_get_album_info(album_id=album_id, client=client, use_cache=False)
        if album_dto is None:
            raise RuntimeError(f"Could not fetch album info for album_id={album_id}")
        dto = AlbumDtoState.from_dto(album_dto)
        entry = cls(dto=dto, max_age_seconds=DEFAULT_CACHE_MAX_AGE_SECONDS)
        save_entity_to_cache("albums", album_id_str, dto.to_dict())
        return entry

    def is_stale(self) -> bool:
        # _dto.get_loaded_at() is a datetime, convert to timestamp for comparison
        return (
            time.time() - self._dto.get_loaded_at().timestamp()
        ) > self._max_age_seconds

    def get_state(self) -> AlbumDtoState:
        if self.is_stale():
            raise StaleAlbumCacheError(
                f"Album cache entry is stale (>{self._max_age_seconds}s)"
            )
        return self._dto

    def ensure_full_loaded(self) -> AlbumCacheEntry:
        """
        Ensures the DTO is of type DETAIL (full). If not, reloads using reload_func.
        If already full, does nothing. If not full and no reload_func is provided, raises exception.
        """
        if self._dto.is_full():
            return self

        # Reload the DTO using the provided function
        album_dto = self.from_cache_or_api()
        # Assumes album_dto is an AlbumResponseDto in DETAIL mode
        self._dto.update(dto=album_dto, load_source=self._dto.get_load_source().DETAIL)
        return self

    def is_empty(self) -> bool:
        """
        Returns True if the album has no assets, False otherwise.
        Does not force reload, uses the current DTO.
        """
        return self.ensure_full_loaded()._dto.is_empty()

    def _get_dto(self) -> AlbumDtoState:
        return self._dto

    def get_asset_uuids(self) -> set[UUID]:
        """
        Returns the set of asset UUIDs in the album, ensuring full DTO is loaded.
        Does not expose DTOs directly.
        """
        return self.ensure_full_loaded()._get_dto().get_asset_uuids()
