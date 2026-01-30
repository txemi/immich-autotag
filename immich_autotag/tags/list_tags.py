from __future__ import annotations

from typeguard import typechecked

from immich_autotag.tags.print_tags import print_tags
from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.types.client_types import ImmichClient


@typechecked
def list_tags(client: ImmichClient) -> TagCollectionWrapper:
    tag_collection = TagCollectionWrapper.get_instance()
    print_tags(tag_collection)
    return tag_collection
