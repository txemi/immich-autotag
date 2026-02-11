from immich_autotag.report.modification_entries_list import ModificationEntriesList
import attrs

from immich_autotag.albums.albums.album_collection_wrapper import (
    AlbumCollectionWrapper,
    AlbumList,
)
from immich_autotag.assets.albums.temporary_manager.naming import is_temporary_album
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.client_types import ImmichClient


@attrs.define(auto_attribs=True, slots=True)
class TemporaryAlbumManager:
    """
    Encapsulates all logic for managing temporary albums in an AlbumCollectionWrapper.
    Receives a reference to the album collection in the constructor.
    """

    _album_collection: AlbumCollectionWrapper

    def detect_empty_temporary_albums(self) -> AlbumList:
        """
        Returns an AlbumList of empty temporary albums to be removed after building the map.
        """
        albums_to_remove = AlbumList()
        albums = self._album_collection.get_albums()
        from immich_autotag.utils.perf.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker.from_args(
            total_assets=len(albums), max_assets=len(albums), skip_n=0
        )
        for idx, album_wrapper in enumerate(albums, 1):
            if tracker.should_log_progress(idx):
                album_url = album_wrapper.get_immich_album_url().geturl()
                progress_msg = tracker.get_progress_description(idx)
                log(
                    f"[TEMP-ALBUM-CHECK] {progress_msg} | Album: '{album_wrapper.get_album_name()}' | URL: {album_url}",
                    level=LogLevel.PROGRESS,
                )
            if album_wrapper.is_empty() and is_temporary_album(
                album_wrapper.get_album_name()
            ):
                albums_to_remove.append(album_wrapper)
        return albums_to_remove

    def remove_empty_temporary_albums(
        self, albums_to_remove: AlbumList, client: ImmichClient
    ) -> ModificationEntriesList:
        """
        Removes empty temporary albums detected after building the map.
        Raises an exception if any album is not temporary (integrity check).
        Collects and propagates the modification entries.
        Logs progress at entry and exit.
        """
        from immich_autotag.report.modification_entries_list import (
            ModificationEntriesList,
        )

        log(
            f"[PROGRESS] Starting removal of {len(albums_to_remove)} empty temporary albums...",
            level=LogLevel.PROGRESS,
        )
        if not albums_to_remove:
            log(
                "[PROGRESS] No empty temporary albums to remove.",
                level=LogLevel.PROGRESS,
            )
            return ModificationEntriesList()
        # Integrity check: all must be temporary
        for album_wrapper in albums_to_remove:
            if not is_temporary_album(album_wrapper.get_album_name()):
                raise RuntimeError(
                    f"Integrity check failed: album '{album_wrapper.get_album_name()}' "
                    f"(id={album_wrapper.get_album_uuid()}) is not temporary but was "
                    f"passed to remove_empty_temporary_albums."
                )
        tag_mod_report = ModificationReport.get_instance()
        modification_entries = ModificationEntriesList()
        for album_wrapper in albums_to_remove:
            try:
                entry = self._album_collection.delete_album(
                    wrapper=album_wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    reason=(
                        "Removed automatically after map build because it was empty "
                        "and temporary"
                    ),
                )
                modification_entries.append(entry)
            except Exception as e:
                album_name = album_wrapper.get_album_name()
                log(
                    f"Failed to remove temporary album '{album_name}': {e}",
                    level=LogLevel.ERROR,
                )
                raise
        removed_count = len(modification_entries.entries())
        log(
            f"[PROGRESS] Finished removal of empty temporary albums. Albums eliminados: {removed_count}",
            level=LogLevel.PROGRESS,
        )
        return modification_entries

    def cleanup_empty_temporary_albums(self, client: ImmichClient):
        """
        Detects and removes empty temporary albums using the temporary album manager.
        """
        albums_to_remove = self.detect_empty_temporary_albums()
        self.remove_empty_temporary_albums(albums_to_remove, client)

    # Private methods and utilities for temporary albums can be added here
