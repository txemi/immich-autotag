from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )
    from immich_autotag.assets.asset_manager import AssetManager
    from immich_autotag.duplicates.duplicate_collection_wrapper import (
        DuplicateCollectionWrapper,
    )
    from immich_autotag.run_output.execution import RunExecution
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper

_instance: "ImmichContext | None" = None


@attrs.define(auto_attribs=True, slots=True)
class ImmichContext:
    _client: "ImmichClientWrapper | None" = attrs.field(default=None)
    _albums_collection: "AlbumCollectionWrapper | None" = attrs.field(default=None)
    _tag_collection: "TagCollectionWrapper | None" = attrs.field(default=None)
    _duplicates_collection: "DuplicateCollectionWrapper | None" = attrs.field(
        default=None
    )
    _asset_manager: "AssetManager | None" = attrs.field(default=None)

    def get_client_wrapper(self) -> ImmichClientWrapper:
        if self._client is None:
            from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

            self._client = ImmichClientWrapper.get_default_instance()
        return self._client

    def get_albums_collection(self) -> "AlbumCollectionWrapper":
        if self._albums_collection is None:
            from immich_autotag.albums.albums.album_collection_wrapper import (
                AlbumCollectionWrapper,
            )

            self._albums_collection = AlbumCollectionWrapper.from_client()
        return self._albums_collection

    def get_tag_collection(self) -> "TagCollectionWrapper":
        if self._tag_collection is None:
            from immich_autotag.tags.list_tags import list_tags

            client = self.get_client_wrapper().get_client()
            self._tag_collection = list_tags(client)
        return self._tag_collection

    def get_duplicates_collection(self) -> "DuplicateCollectionWrapper":
        if self._duplicates_collection is None:
            from immich_autotag.duplicates.load_duplicates_collection import (
                load_duplicates_collection,
            )

            client = self.get_client_wrapper().get_client()
            self._duplicates_collection = load_duplicates_collection(client)
        return self._duplicates_collection

    def get_asset_manager(self) -> "AssetManager":
        if self._asset_manager is None:
            from immich_autotag.assets.asset_manager import AssetManager

            client = self.get_client_wrapper().get_client()
            self._asset_manager = AssetManager(client=client)
        return self._asset_manager

    @staticmethod
    @typechecked
    def get_run_output_dir() -> "RunExecution":
        """
        Returns the RunExecution object for the current run (logs_local/<timestamp>_PID<pid>),
        using the same logic as RunOutputManager.get_run_output_dir().
        """
        from immich_autotag.run_output.manager import RunOutputManager

        return RunOutputManager.current().get_run_output_dir()

    def __attrs_post_init__(self):
        global _instance
        if _instance is not None:
            raise RuntimeError(
                "ImmichContext instance already exists. Use get_default_instance()."
            )
        _instance = self

    @staticmethod
    @typechecked
    def get_default_instance() -> "ImmichContext":
        global _instance
        if _instance is None:
            _instance = ImmichContext()
        return _instance

    # create_default_instance is no longer needed; use get_default_instance()

    @staticmethod
    def get_default_client() -> "ImmichClientWrapper":
        """Returns the ImmichClientWrapper from the global singleton context."""
        ctx = ImmichContext.get_default_instance()
        return ctx.get_client_wrapper()
