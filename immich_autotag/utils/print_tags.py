from typing import List
from immich_client.models.tag_response_dto import TagResponseDto

def print_tags(tags: List[TagResponseDto]) -> None:
    print("Tags:")
    for tag in tags:
        print(f"- {tag.name}")
    print(f"Total tags: {len(tags)}\n")
    MIN_TAGS = 57
    if len(tags) < MIN_TAGS:
        raise Exception(
            f"ERROR: Unexpectedly low number of tags: {len(tags)} < {MIN_TAGS}"
        )
