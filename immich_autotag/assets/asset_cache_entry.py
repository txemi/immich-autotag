
import datetime
from typing import Any, Dict
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
        def from_cache_or_api(
            cls,
            asset_id: Any,
            context: Any,
            max_age_seconds: int = 3600,
            use_cache: bool = True,
        ) -> "AssetCacheEntry":
            """
            Intenta cargar el asset desde la caché de disco; si no está o está corrupto, recarga desde la API y guarda en caché.
            """
            from immich_client.models.asset_response_dto import AssetResponseDto
            from immich_autotag.utils.api_disk_cache import get_entity_from_cache, save_entity_to_cache
            from immich_autotag.api.immich_proxy.assets import get_asset_info

            cache_data = get_entity_from_cache("assets", str(asset_id), use_cache=use_cache)
            if cache_data is not None:
                try:
                    dto = AssetResponseDto.from_dict(cache_data)
                    state = AssetDtoState(dto, AssetDtoType.FULL)
                    return cls.from_state(state, max_age_seconds=max_age_seconds)
                except Exception:
                    pass  # Si la caché está corrupta, recarga de API
            # Si no está en caché o está corrupto, recarga desde API
            if context is not None and hasattr(context, "client"):
                client = context.client
            elif hasattr(context, "get_client"):
                client = context.get_client()
            else:
                raise ValueError("Context must provide a .client or .get_client() method")
            dto = get_asset_info(asset_id, client, use_cache=False)
            if dto is None:
                raise RuntimeError(f"get_asset_info returned None for asset id={asset_id}")
            state = AssetDtoState(dto, AssetDtoType.FULL)
            save_entity_to_cache("assets", str(asset_id), dto.to_dict())
            return cls.from_state(state, max_age_seconds=max_age_seconds)

        @classmethod
        def from_api(
            cls, asset_id: Any, context: Any, max_age_seconds: int = 3600
        ) -> "AssetCacheEntry":
            """
            Crea un AssetCacheEntry cargando el asset desde la caché o la API (siempre FULL).
            """
            return cls.from_cache_or_api(asset_id, context, max_age_seconds=max_age_seconds, use_cache=True)
        from immich_autotag.assets.asset_dto_state import AssetDtoState, AssetDtoType
        from immich_autotag.utils.api_disk_cache import (
            get_entity_from_cache,
            save_entity_to_cache,
        )

        cache_data = get_entity_from_cache("assets", str(asset_id), use_cache=use_cache)
        if cache_data is not None:
            try:
                dto = AssetResponseDto.from_dict(cache_data)
                state = AssetDtoState(dto, AssetDtoType.FULL)
                return cls.from_state(state, max_age_seconds=max_age_seconds)
            except Exception:
                pass  # Si la caché está corrupta, recarga de API
        # Si no está en caché o está corrupto, recarga desde API
        from immich_autotag.api.immich_proxy.assets import (
            get_asset_info as proxy_get_asset_info,
        )

        dto = proxy_get_asset_info(asset_id, context.client, use_cache=False)
        if dto is None:
            raise RuntimeError(f"get_asset_info returned None for asset id={asset_id}")
        state = AssetDtoState(dto, AssetDtoType.FULL)
        # Guardar en caché
        save_entity_to_cache("assets", str(asset_id), dto.to_dict())
        return cls.from_state(state, max_age_seconds=max_age_seconds)

