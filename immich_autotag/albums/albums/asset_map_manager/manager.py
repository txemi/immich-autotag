import attrs
from immich_autotag.albums.albums.album_list import AlbumList
from immich_autotag.albums.albums.asset_to_albums_map import AssetToAlbumsMap
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper

@attrs.define(auto_attribs=True, slots=True)
class AssetMapManager:
    """
    Encapsulates all logic for building, updating y sincronizar el mapeo asset_id -> álbumes.
    """
    _collection: "AlbumCollectionWrapper"
    _asset_to_albums_map: AssetToAlbumsMap = attrs.Factory(AssetToAlbumsMap)

    def _build_map(self) -> AssetToAlbumsMap:
        """Construye el mapeo asset_id -> álbumes desde cero."""
        asset_map = AssetToAlbumsMap()
        assert (
            len(self.collection._albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."

        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

        client = ImmichClientWrapper.get_default_instance().get_client()
        albums = self.collection.get_albums()
        total = len(albums)
        tracker = None
        if total > 0:
            from immich_autotag.utils.perf.performance_tracker import PerformanceTracker
            tracker = PerformanceTracker.from_total(total)
        for idx, album_wrapper in enumerate(albums, 1):
            if album_wrapper.is_empty():
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log
                log(
                    f"Album '{album_wrapper.get_album_name()}' "
                    f"has no assets after forced reload.",
                    level=LogLevel.WARNING,
                )
                if album_wrapper.get_asset_uuids():
                    album_url = album_wrapper.get_immich_album_url().geturl()
                    raise RuntimeError(
                        f"[DEBUG] Anomalous behavior: Album "
                        f"'{album_wrapper.get_album_name()}' (URL: {album_url}) "
                        "had empty asset_ids after initial load, "
                        "but after a redundant reload it now has assets. "
                        "This suggests a possible synchronization or lazy loading bug. "
                        "Please review the album loading logic."
                    )
                from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
                if is_temporary_album(album_wrapper.get_album_name()):
                    log(
                        f"Temporary album '{album_wrapper.get_album_name()}' "
                        f"marked for removal after map build.",
                        level=LogLevel.WARNING,
                    )
            if tracker and tracker.should_log_progress(idx):
                progress_msg = tracker.get_progress_description(idx)
                from immich_autotag.logging.levels import LogLevel
                from immich_autotag.logging.utils import log
                log(
                    f"[ALBUM-MAP-BUILD][PROGRESS] {progress_msg}. Album "
                    f"'{album_wrapper.get_album_name()}' reloaded with "
                    f"{len(album_wrapper.get_asset_uuids())} assets.",
                    level=LogLevel.PROGRESS,
                )
            asset_map.add_album_for_asset_ids(album_wrapper)
        # Limpieza de temporales vacíos
        temp_manager = self.collection._get_temporary_album_manager()
        albums_to_remove = temp_manager.detect_empty_temporary_albums()
        temp_manager.remove_empty_temporary_albums(albums_to_remove, client)
        self._asset_to_albums_map = asset_map
        return asset_map

    def rebuild_map(self) -> None:
        """Reconstruye el mapeo desde cero y lo actualiza en el manager."""
        self._asset_to_albums_map = self.build_map()

    def _remove_album(self, album_wrapper: AlbumResponseWrapper) -> bool:
        """Elimina un álbum del mapeo y actualiza el estado."""
        self._asset_to_albums_map.remove_album_for_asset_ids(album_wrapper)
        return True

    def get_map(self) -> AssetToAlbumsMap:
        """Devuelve el mapeo actual."""
        return self._asset_to_albums_map
