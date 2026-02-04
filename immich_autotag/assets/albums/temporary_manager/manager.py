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
        for album_wrapper in self._album_collection.get_albums():
            if album_wrapper.is_empty() and is_temporary_album(
                album_wrapper.get_album_name()
            ):
                albums_to_remove.append(album_wrapper)
        return albums_to_remove

    def remove_empty_temporary_albums(
        self, albums_to_remove: AlbumList, client: ImmichClient
    ):
        """
        Removes empty temporary albums detected after building the map.
        Raises an exception if any of them is not temporary (integrity).
        """
        if not albums_to_remove:
            return
        # Integrity check: all must be temporary
        for album_wrapper in albums_to_remove:
            if not is_temporary_album(album_wrapper.get_album_name()):
                raise RuntimeError(
                    f"Integrity check failed: album '{album_wrapper.get_album_name()}' "
                    f"(id={album_wrapper.get_album_uuid()}) is not temporary but was "
                    f"passed to remove_empty_temporary_albums."
                )
        tag_mod_report = ModificationReport.get_instance()
        for album_wrapper in albums_to_remove:
            try:
                self._album_collection.delete_album(
                    wrapper=album_wrapper,
                    client=client,
                    tag_mod_report=tag_mod_report,
                    reason=(
                        "Removed automatically after map build because it was empty "
                        "and temporary"
                    ),
                )
            except Exception as e:
                album_name = album_wrapper.get_album_name()
                log(
                    f"Failed to remove temporary album '{album_name}': {e}",
                    level=LogLevel.ERROR,
                )
                raise

    # Métodos privados y utilidades específicas para temporales pueden añadirse aquí
