from __future__ import annotations

from typing import List
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked




@typechecked
def print_tags(tags: list[TagResponseDto]) -> None:
    print("Tags:")
    for tag in tags:
        print(f"- {tag.name}")
    print(f"Total tags: {len(tags)}\n")
    MIN_TAGS = 57
    if len(tags) < MIN_TAGS:
        raise Exception(
            f"ERROR: Unexpectedly low number of tags: {len(tags)} < {MIN_TAGS}"
        )
