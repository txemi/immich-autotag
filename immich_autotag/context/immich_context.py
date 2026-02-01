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

_instance = None
_instance_created = False


@attrs.define(auto_attribs=True, slots=True)
class ImmichContext:
    _client: "ImmichClientWrapper" = attrs.field()
    _albums_collection: "AlbumCollectionWrapper" = attrs.field()
    _tag_collection: "TagCollectionWrapper" = attrs.field()
    _duplicates_collection: "DuplicateCollectionWrapper" = attrs.field()
    _asset_manager: "AssetManager" = attrs.field()

    def get_client_wrapper(self) -> ImmichClientWrapper:
        return self._client

    def get_albums_collection(self) -> "AlbumCollectionWrapper":
        return self._albums_collection

    def get_tag_collection(self) -> "TagCollectionWrapper":
        return self._tag_collection

    def get_duplicates_collection(self) -> "DuplicateCollectionWrapper":
        return self._duplicates_collection

    def get_asset_manager(self) -> "AssetManager":
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
        global _instance, _instance_created
        # Explicit type validation to avoid circular import issues
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )
        from immich_autotag.assets.asset_manager import AssetManager
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.duplicates.duplicate_collection_wrapper import (
            DuplicateCollectionWrapper,
        )
        from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper

        if not isinstance(self._client, ImmichClientWrapper):
            raise TypeError(
                f"_client debe ser ImmichClientWrapper, no {type(self._client)}"
            )
        if not isinstance(self._albums_collection, AlbumCollectionWrapper):
            raise TypeError(
                f"_albums_collection debe ser AlbumCollectionWrapper, no {type(self._albums_collection)}"
            )
        if not isinstance(self._tag_collection, TagCollectionWrapper):
            raise TypeError(
                f"_tag_collection debe ser TagCollectionWrapper, no {type(self._tag_collection)}"
            )
        if not isinstance(self._duplicates_collection, DuplicateCollectionWrapper):
            raise TypeError(
                f"_duplicates_collection debe ser DuplicateCollectionWrapper, no {type(self._duplicates_collection)}"
            )
        if not isinstance(self._asset_manager, AssetManager):
            raise TypeError(
                f"_asset_manager debe ser AssetManager, no {type(self._asset_manager)}"
            )
        # Reserved global variables _instance and _instance_created are required for singleton pattern
        if _instance_created:
            print(
                "[INFO] Reserved global variable _instance_created is in use for singleton enforcement."
            )
            raise RuntimeError(
                "ImmichContext instance already exists. Use get_instance()."
            )
        _instance_created = True
        print("[INFO] Assigning self to reserved global variable _instance.")
        _instance = self

    @staticmethod
    @typechecked
    def get_default_instance() -> "ImmichContext":
        global _instance
        # Reserved global variable _instance is required for singleton pattern
        if _instance is None:
            print(
                "[INFO] Reserved global variable _instance is None, ImmichContext not initialized."
            )
            raise RuntimeError(
                "ImmichContext not initialized. Create an instance first."
            )
        # No explicit assignment needed for F824
        return _instance

    @staticmethod
    @typechecked
    def create_default_instance(
        client: "ImmichClientWrapper",
        albums_collection: "AlbumCollectionWrapper",
        tag_collection: "TagCollectionWrapper",
        duplicates_collection: "DuplicateCollectionWrapper",
        asset_manager: "AssetManager",
    ) -> "ImmichContext":
        """
        Factory method to create the singleton ImmichContext instance.
        This should be called only once at application startup.
        Automatically registers itself as the singleton.
        """
        global _instance, _instance_created
        # Reserved global variables _instance and _instance_created are required for singleton pattern
        if _instance_created:
            print(
                "[INFO] Reserved global variable _instance_created is in use for singleton enforcement."
            )
            raise RuntimeError(
                "ImmichContext instance already exists. Use get_default_instance()."
            )
        # Create instance (will call __attrs_post_init__ which sets the singleton)
        instance = ImmichContext(
            client=client,
            albums_collection=albums_collection,
            tag_collection=tag_collection,
            duplicates_collection=duplicates_collection,
            asset_manager=asset_manager,
        )
        # No explicit assignment needed for F824
        _instance = instance
        _instance_created = True
        return instance

    @staticmethod
    def get_default_client() -> "ImmichClientWrapper":
        """Returns the ImmichClientWrapper from the global singleton context."""
        ctx = ImmichContext.get_default_instance()
        return ctx.get_client_wrapper()
