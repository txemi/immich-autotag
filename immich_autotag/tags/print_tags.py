from __future__ import annotations

from typeguard import typechecked

from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


@typechecked
def print_tags(tag_collection: TagCollectionWrapper) -> None:
    print("Tags:")
    for tag in tag_collection:
        print(f"- {tag.name}")
    print(f"Total tags: {len(tag_collection)}\n")
