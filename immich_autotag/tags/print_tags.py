from __future__ import annotations

from typeguard import typechecked

from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper


@typechecked
def print_tags(tag_collection: TagCollectionWrapper) -> None:
    total = len(tag_collection)
    if total <= 20:
        print("Tags:")
        for tag in tag_collection:
            print(f"- {tag.get_name()}")
    print(f"Total tags: {total}\n")
