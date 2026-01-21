from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.types import ImmichClient

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )
    from immich_autotag.assets.asset_manager import AssetManager
    from immich_autotag.duplicates.duplicate_collection_wrapper import (
        DuplicateCollectionWrapper,
    )
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


_instance = None
_instance_created = False


@attrs.define(auto_attribs=True, slots=True)
class ImmichContext:

    client: ImmichClient = attrs.field(
        validator=attrs.validators.instance_of((ImmichClient,))
    )
    albums_collection: "AlbumCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    tag_collection: "TagCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    duplicates_collection: "DuplicateCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    asset_manager: "AssetManager" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )

    def __attrs_post_init__(self):
        global _instance, _instance_created
        if _instance_created:
            raise RuntimeError(
                "ImmichContext instance already exists. Use get_instance()."
            )
        _instance_created = True
        _instance = self

    @staticmethod
    @typechecked
    def get_instance() -> "ImmichContext":
        global _instance
        if _instance is None:
            raise RuntimeError(
                "ImmichContext not initialized. Create an instance first."
            )
        return _instance

    @staticmethod
    @typechecked
    def create_instance(
        client: ImmichClient,
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
        if _instance_created:
            raise RuntimeError(
                "ImmichContext instance already exists. Use get_instance()."
            )
        # Create instance (will call __attrs_post_init__ which sets the singleton)
        instance = ImmichContext(
            client=client,
            albums_collection=albums_collection,
            tag_collection=tag_collection,
            duplicates_collection=duplicates_collection,
            asset_manager=asset_manager,
        )
        return instance

    @staticmethod
    def get_default_client():
        """Returns the ImmichClient from the global singleton context."""
        ctx = ImmichContext.get_instance()
        return ctx.client
