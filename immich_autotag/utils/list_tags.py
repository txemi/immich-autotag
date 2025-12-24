from __future__ import annotations

from immich_client import Client
from typeguard import typechecked
from immich_autotag.core.tag_collection_wrapper import TagCollectionWrapper
from immich_autotag.utils.print_tags import print_tags

@typechecked
def list_tags(client: Client) -> TagCollectionWrapper:
    tag_collection = TagCollectionWrapper.from_api(client)
    print_tags(tag_collection.tags)
    return tag_collection
