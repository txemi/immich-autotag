from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from immich_client import Client

if TYPE_CHECKING:
    from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper
    from immich_autotag.assets.asset_manager import AssetManager
    from immich_autotag.duplicates.duplicate_collection_wrapper import (
        DuplicateCollectionWrapper,
    )
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ImmichContext:
    client: Client = attrs.field(validator=attrs.validators.instance_of(Client))
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
