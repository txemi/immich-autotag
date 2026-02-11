from typing import TYPE_CHECKING

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.asset_to_albums_map import AssetToAlbumsMap

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )


@attrs.define(auto_attribs=True, slots=True)
class AssetMapManager:
    """
    Encapsulates all logic for building, updating, and synchronizing the asset_id -> albums mapping.
    """

    _collection: "AlbumCollectionWrapper" = attrs.field(
        init=True,
        metadata={"required": True},
    )
    _asset_to_albums_map: AssetToAlbumsMap = attrs.field(
        init=False,
        factory=AssetToAlbumsMap,
        repr=lambda x: len(x),
        eq=False,
        metadata={"internal": True},
    )
    _is_map_loaded: bool = attrs.field(
        init=False,
        default=False,
        repr=True,
        eq=False,
        metadata={"internal": True},
    )

    # Method removed: now handled by TemporaryAlbumManager
    def _build_map(self) -> AssetToAlbumsMap:
        """Builds the asset_id -> albums mapping from scratch."""
        asset_map = AssetToAlbumsMap()
        assert (
            len(self._collection._albums) > 0
        ), "AlbumCollectionWrapper must have at least one album to build asset map."

        albums = self._collection.get_albums()
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
                from immich_autotag.assets.albums.temporary_manager.naming import (
                    is_temporary_album,
                )

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
        # Cleanup of empty temporary albums

        self._asset_to_albums_map = asset_map
        self._is_map_loaded = True
        return asset_map

    def rebuild_map(self) -> None:
        """Rebuilds the mapping from scratch and updates it in the manager."""
        self._is_map_loaded = False
        self._asset_to_albums_map = self._build_map()

    def _remove_album(self, album_wrapper: AlbumResponseWrapper) -> bool:
        """Removes an album from the mapping and updates the state."""
        self._asset_to_albums_map.remove_album_for_asset_ids(album_wrapper)
        return True

    def _load_map(self) -> None:
        """Loads the map if it is not loaded (internal use)."""
        if not self._is_map_loaded:
            self._build_map()

    def get_map(self) -> AssetToAlbumsMap:
        """Returns the current mapping. Ensures the map is loaded."""
        self._load_map()
        return self._asset_to_albums_map

    def clear(self):
        """Clears the current mapping."""
        self._asset_to_albums_map.clear()
        self._is_map_loaded = False
