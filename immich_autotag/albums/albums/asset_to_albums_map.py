from typing import Iterator, MutableMapping

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_list import AlbumList

from .album_list import AlbumList


class AssetToAlbumsMap(MutableMapping[str, AlbumList]):
    """
    Mapa de asset_id (str) a AlbumList.
    La clave del mapa es el asset_id (string) de cada asset.
    El valor es una lista de álbumes (AlbumList) que contienen ese asset.
    Permite consultas O(1) para saber a qué álbumes pertenece un asset.
    """

    def __init__(self):
        self._map: dict[str, AlbumList] = dict()

    def __getitem__(self, key: str) -> AlbumList:
        return self._map[key]

    def __setitem__(self, key: str, value: AlbumList) -> None:
        self._map[key] = value

    def __delitem__(self, key: str) -> None:
        del self._map[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._map)

    def __len__(self) -> int:
        return len(self._map)

    # Rely on MutableMapping.get implementation; avoid overriding overloaded signature.

    def clear(self) -> None:
        self._map.clear()

    def items(self):
        return self._map.items()

    def keys(self):
        return self._map.keys()

    def values(self):
        return self._map.values()

    def __contains__(self, key: object) -> bool:
        # Use object type to match the Container/Mapping protocol
        try:
            return key in self._map
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"AssetToAlbumsMap({self._map!r})"

    @typechecked
    def remove_album_for_asset_ids(self, album_wrapper: AlbumResponseWrapper) -> None:
        for asset_id in album_wrapper.get_asset_ids():
            if asset_id in self:
                album_list = self[asset_id]
                album_list.remove_album(album_wrapper)
                if not album_list:
                    del self[asset_id]
