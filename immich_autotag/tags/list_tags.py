from __future__ import annotations

from immich_client import Client
from typeguard import typechecked

from immich_autotag.tags.print_tags import print_tags
from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


@typechecked
def list_tags(client: Client) -> TagCollectionWrapper:
    tag_collection = TagCollectionWrapper.from_api(client)
    print_tags(tag_collection)
    return tag_collection
