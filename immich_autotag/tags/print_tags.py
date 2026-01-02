from __future__ import annotations

from typeguard import typechecked

from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


@typechecked
def print_tags(tag_collection: TagCollectionWrapper) -> None:
    print("Tags:")
    for tag in tag_collection:
        print(f"- {tag.name}")
    print(f"Total tags: {len(tag_collection)}\n")
    MIN_TAGS = 57
    if len(tag_collection) < MIN_TAGS:
        raise Exception(
            f"ERROR: Unexpectedly low number of tags: {len(tag_collection)} < {MIN_TAGS}"
        )
