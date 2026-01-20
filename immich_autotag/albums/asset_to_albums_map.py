from typing import Iterator, MutableMapping

from .album_list import AlbumList


class AssetToAlbumsMap(MutableMapping[str, AlbumList]):
    def __init__(self):
        self._map = dict()

    def __getitem__(self, key: str) -> AlbumList:
        return self._map[key]

    def __setitem__(self, key: str, value: AlbumList):
        self._map[key] = value

    def __delitem__(self, key: str):
        del self._map[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._map)

    def __len__(self) -> int:
        return len(self._map)

    # Rely on MutableMapping.get implementation; avoid overriding overloaded signature.

    def clear(self):
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

    def __repr__(self):
        return f"AssetToAlbumsMap({self._map!r})"
