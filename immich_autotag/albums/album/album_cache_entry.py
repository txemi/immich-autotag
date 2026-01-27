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

    pass


class StaleAlbumCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""


@attrs.define(auto_attribs=True, kw_only=True, slots=True)
class AlbumCacheEntry:

    _dto: AlbumDtoState
    _max_age_seconds: int = DEFAULT_CACHE_MAX_AGE_SECONDS

    @classmethod
    def _from_cache_or_api(
        cls,
        album_id: "UUID",
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> "AlbumResponseDto":
        """
        Attempts to load the album from cache. If it is stale or does not exist, this method must be completed with an API fetch implementation.
        Returns an AlbumDtoState directly.
        """
        album_id_str = str(album_id)
        cache_data = get_entity_from_cache("albums", album_id_str, use_cache=use_cache)
        if cache_data is not None:
            try:
                from immich_client.models.album_response_dto import AlbumResponseDto
                album_dto = AlbumResponseDto.from_dict(cache_data)
                from immich_autotag.albums.album.album_dto_state import AlbumLoadSource
                dto = AlbumDtoState(
                    _dto=album_dto,
                    _load_source=AlbumLoadSource.DETAIL,
                )
                # Check staleness using a temp AlbumCacheEntry
                if not dto.is_stale():
                    return dto
            except Exception:
                pass  # If the cache is corrupt, reload from API
        # API fetch logic: call proxy_get_album_info using the default Immich client
        from immich_autotag.api.immich_proxy.albums import proxy_get_album_info
        from immich_autotag.context.immich_context import ImmichContext
        from immich_autotag.albums.album.album_dto_state import AlbumLoadSource

        client = ImmichContext.get_default_instance().get_client_wrapper().get_client()
        album_dto = proxy_get_album_info(
            album_id=album_id, client=client, use_cache=False
        )
        if album_dto is None:
            raise RuntimeError(f"Could not fetch album info for album_id={album_id}")

        # Use to_dict for serialization
        save_entity_to_cache("albums", album_id_str, album_dto.to_dict())
        return album_dto

    def is_stale(self) -> bool:
        # _dto.get_loaded_at() is a datetime, convert to timestamp for comparison
        return self._dto._is_stale()

    def get_state(self) -> AlbumDtoState:
        if self.is_stale():
            raise StaleAlbumCacheError(
                f"Album cache entry is stale (>{self._max_age_seconds}s)"
            )
        return self._dto

    def ensure_full_loaded(self) -> "AlbumCacheEntry":
        """
        Ensures the DTO is of type DETAIL (full). If not, reloads using _from_cache_or_api.
        If already full, does nothing. If not full and no reload_func is provided, raises exception.
        """
        if self._dto.is_full():
            return self

        # Reload the DTO using the new DTO returned by _from_cache_or_api
        new_dto: AlbumResponseDto = self._from_cache_or_api(album_id=self._dto.get_album_id())
        # Use public API for update
        self._dto.update(dto=new_dto, load_source=new_dto.get_load_source())
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
