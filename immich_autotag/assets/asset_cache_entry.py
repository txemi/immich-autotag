ASSET_CACHE_KEY = "assets"
import datetime
from uuid import UUID

import attrs

from immich_autotag.assets.asset_dto_state import AssetDtoState, AssetDtoType


class StaleAssetCacheError(Exception):
    """Raised when a cache entry is stale and cannot be used."""

    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetCacheEntry:


    """
    Encapsula el estado cacheado de un asset, con lógica de frescura y recarga.
    Los atributos son privados; acceso solo mediante métodos públicos.
    """

    _state: AssetDtoState
    _max_age_seconds: int = 3600  # Por defecto, 1h

    def is_stale(self) -> bool:
        age = (datetime.datetime.now() - self._state.loaded_at).total_seconds()
        return age > self._max_age_seconds

    def get_state(self) -> AssetDtoState:
        if self.is_stale():
            raise StaleAssetCacheError(
                f"Asset cache entry is stale (>{self._max_age_seconds}s)"
            )
        return self._state

    def get_loaded_at(self) -> datetime.datetime:
        return self._state.loaded_at

    @classmethod
    def _from_cache_or_api(
        cls,
        asset_id: UUID,
        *,
        max_age_seconds: int = 3600,
        use_cache: bool = True,
    ) -> "AssetCacheEntry":
        """
        Intenta cargar el asset desde la caché de disco; si no está o está corrupto, recarga desde la API y guarda en caché.
        asset_id debe ser un UUID.
        """
        from immich_client.models.asset_response_dto import AssetResponseDto

        from immich_autotag.api.immich_proxy.assets import get_asset_info
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.utils.api_disk_cache import (
            get_entity_from_cache,
            save_entity_to_cache,
        )

        cache_data = get_entity_from_cache(ASSET_CACHE_KEY, str(asset_id), use_cache=use_cache)
        if cache_data is not None:
            try:
                dto = AssetResponseDto.from_dict(cache_data)
                state = AssetDtoState(dto, AssetDtoType.FULL)
                return cls._from_state(state, max_age_seconds=max_age_seconds)
            except Exception:
                pass  # Si la caché está corrupta, recarga de API
        # Si no está en caché o está corrupto, recarga desde API
        client = ImmichClientWrapper.get_default_instance().get_client()
        dto = get_asset_info(asset_id, client, use_cache=False)
        if dto is None:
            raise RuntimeError(f"get_asset_info returned None for asset id={asset_id}")
        state = AssetDtoState(dto, AssetDtoType.FULL)
        save_entity_to_cache(ASSET_CACHE_KEY, str(asset_id), dto.to_dict())
        return cls._from_state(state, max_age_seconds=max_age_seconds)


    @classmethod
    def _from_state(
        cls, state: AssetDtoState, max_age_seconds: int = 3600
    ) -> "AssetCacheEntry":
        """
        Crea un AssetCacheEntry a partir de un estado ya existente (privado).
        """
        return cls(_state=state, _max_age_seconds=max_age_seconds)

    def to_cache_dict(self) -> dict:
        """
        Serializa la entrada de caché a un diccionario.
        """
        return {
            "state": (
                self._state.to_cache_dict()
                if hasattr(self._state, "to_cache_dict")
                else self._state
            ),
            "max_age_seconds": self._max_age_seconds,
        }

    @classmethod
    def from_cache_dict(cls, data: dict) -> "AssetCacheEntry":
        """
        Hidrata una entrada de caché desde un diccionario serializado.
        """
        state = (
            AssetDtoState.from_cache_dict(data["state"])
            if hasattr(AssetDtoState, "from_cache_dict")
            else data["state"]
        )
        return cls(_state=state, _max_age_seconds=data.get("max_age_seconds", 3600))

    def ensure_full_asset_loaded(self, context: "ImmichContext") -> AssetDtoState:
        """
        Ensures the asset is fully loaded (type FULL). If not, fetches from API and updates the cache entry.
        """
        state = self.get_state()
        from immich_autotag.assets.asset_dto_state import AssetDtoType
        if state.type == AssetDtoType.FULL:
            return state

        self._reload_from_api(context)
        return self._state

    def _reload_from_api(self, context: "ImmichContext") -> "AssetCacheEntry":
        """
        Reloads the asset state from the API and updates the cache entry. Returns self for convenience.
        """
        from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
        asset_id = self._state.dto.id  # Assumes dto has id attribute
        refreshed = AssetResponseWrapper.from_api(asset_id, context)
        self._state = refreshed._cache_entry.get_state()
        return self