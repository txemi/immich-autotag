from __future__ import annotations

import time
from typing import TYPE_CHECKING
from uuid import UUID

import attrs

from immich_autotag.albums.album.album_dto_state import AlbumDtoState
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
    _max_age_seconds: int = 3600

    @classmethod
    def from_cache_or_api(
        cls,
        album_id: "UUID",
        fetch_album_func,
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> "AlbumCacheEntry":
        """
        Intenta cargar el álbum desde caché. Si está obsoleto o no existe, lo recarga usando fetch_album_func.
        """
        # Always use string representation for cache keys, but require UUID type for album_id
        album_id_str = str(album_id)
        cache_data = get_entity_from_cache("albums", album_id_str, use_cache=use_cache)
        if cache_data is not None:
            try:
                dto = AlbumDtoState.from_dict(cache_data)
                entry = cls(dto=dto, max_age_seconds=max_age_seconds)
                if not entry.is_stale():
                    return entry
            except Exception:
                pass  # Si la caché está corrupta, recarga de API
        # Si no está en caché o está corrupto, recarga desde API
        album_dto: AlbumResponseDto = fetch_album_func(album_id)
        dto = AlbumDtoState.from_dto(album_dto)
        entry = cls(dto=dto, max_age_seconds=max_age_seconds)
        save_entity_to_cache("albums", album_id_str, dto.to_dict())
        return entry

    def is_stale(self) -> bool:
        # _dto.get_loaded_at() es un datetime, lo convertimos a timestamp para comparar
        return (
            time.time() - self._dto.get_loaded_at().timestamp()
        ) > self._max_age_seconds

    def get_state(self) -> AlbumDtoState:
        if self.is_stale():
            raise StaleAlbumCacheError(
                f"Album cache entry is stale (>{self._max_age_seconds}s)"
            )
        return self._dto
