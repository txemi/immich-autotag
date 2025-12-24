from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from immich_client import Client

if TYPE_CHECKING:
    from .album_collection_wrapper import AlbumCollectionWrapper
    from .tag_collection_wrapper import TagCollectionWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class ImmichContext:
    client: Client = attrs.field(validator=attrs.validators.instance_of(Client))
    albums_collection: "AlbumCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
    tag_collection: "TagCollectionWrapper" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )
