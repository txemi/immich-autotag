from typing import Iterator, MutableMapping
from uuid import UUID

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_list import AlbumList


class AssetToAlbumsMap(MutableMapping[UUID, AlbumList]):
    """
    Map from asset_id (str) to AlbumList.
    The map key is the asset_id (string) of each asset.
    The value is a list of albums (AlbumList) that contain that asset.
    Allows O(1) queries to know which albums an asset belongs to.
    """

    def __init__(self):
        self._map: dict[UUID, AlbumList] = dict()

    # Rely on MutableMapping.get implementation; avoid overriding overloaded signature.

    def clear(self) -> None:
        self._map.clear()

    def items(self):
        return self._map.items()

    def keys(self):
        return self._map.keys()

    def values(self):
        return self._map.values()

    @typechecked
    def remove_album_for_asset_ids(self, album_wrapper: AlbumResponseWrapper) -> None:
        """
        Remove the album from all asset lists. If the album is full, use its asset UUIDs directly.
        If not full, remove the album from all AlbumLists in the map (slower, but
        avoids triggering a full load).
        """
        raise NotImplementedError("revisar")
        if album_wrapper.has_loaded_assets():
            for asset_uuid in album_wrapper.get_asset_uuids():
                if asset_uuid in self:
                    album_list = self[asset_uuid]
                    album_list.remove_album(album_wrapper)
                    if not album_list:
                        del self[asset_uuid]
        else:
            # Not full: must scan all asset lists and remove the album from each
            to_remove = []
            for asset_uuid, album_list in self._map.items():
                album_list.remove_album(album_wrapper)
                if not album_list:
                    to_remove.append(asset_uuid)
            for asset_uuid in to_remove:
                del self._map[asset_uuid]

    @typechecked
    def add_album_for_asset_ids(self, album_wrapper: AlbumResponseWrapper) -> None:
        """
        Adds the given album to the map for all its asset UUIDs. Creates a new
        AlbumList if needed.
        """
        for asset_uuid in album_wrapper.get_asset_uuids():
            if asset_uuid not in self:
                self[asset_uuid] = AlbumList()
            self[asset_uuid].append(album_wrapper)

    @typechecked
    def get_from_uuid(self, asset_uuid: UUID) -> AlbumList:
        """
        Returns the AlbumList for the given asset UUID, or an empty AlbumList if none.
        """
        if asset_uuid in self:
            return self[asset_uuid]
        else:
            return AlbumList()

    def __getitem__(self, key: UUID) -> AlbumList:
        if not isinstance(key, UUID):
            raise TypeError(
                f"AssetToAlbumsMap keys must be UUID, got {type(key).__name__}"
            )
        return self._map[key]

    def __setitem__(self, key: UUID, value: AlbumList) -> None:
        if not isinstance(key, UUID):
            raise TypeError(
                f"AssetToAlbumsMap keys must be UUID, got {type(key).__name__}"
            )
        self._map[key] = value

    def __delitem__(self, key: UUID) -> None:
        if not isinstance(key, UUID):
            raise TypeError(
                f"AssetToAlbumsMap keys must be UUID, got {type(key).__name__}"
            )
        del self._map[key]

    def __iter__(self) -> Iterator[UUID]:
        return iter(self._map)

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, UUID):
            raise TypeError(
                f"AssetToAlbumsMap keys must be UUID, got {type(key).__name__}"
            )
        return key in self._map

    def __len__(self) -> int:
        return len(self._map)

    def __repr__(self) -> str:
        return f"AssetToAlbumsMap({self._map!r})"
