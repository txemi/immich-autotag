import attrs
from immich_client import Client
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked

from immich_autotag.tags.tag_response_wrapper import TagWrapper


@attrs.define(auto_attribs=True, slots=True)
class TagCollectionWrapper:
    tags: list[TagWrapper] = attrs.field(validator=attrs.validators.instance_of(list))

    @typechecked
    def create_tag_if_not_exists(self, name: str, client) -> TagWrapper:
        """
        Creates the tag in Immich if it doesn't exist and adds it to the local collection.
        Returns the corresponding TagResponseDto.
        """
        tag = self.find_by_name(name)
        if tag is not None:
            return tag
        from immich_client.api.tags import create_tag
        from immich_client.models.tag_create_dto import TagCreateDto

        tag_create = TagCreateDto(name=name)
        new_tag_dto = create_tag.sync(client=client, body=tag_create)
        new_tag = TagWrapper(new_tag_dto)
        self.tags.append(new_tag)
        return new_tag

    @staticmethod
    @typechecked
    def from_api(client: Client) -> "TagCollectionWrapper":
        """
        Builds a TagCollectionWrapper instance by fetching tags from the Immich API.
        """
        from immich_client.api.tags import get_all_tags

        tags_dto = get_all_tags.sync(client=client)
        tags = [TagWrapper(tag) for tag in tags_dto]
        return TagCollectionWrapper(tags=tags)

    @typechecked
    def find_by_name(self, name: str) -> TagWrapper | None:
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

    @typechecked
    def __contains__(self, name: str) -> bool:
        return any(tag.name == name for tag in self.tags)

    @typechecked
    def __len__(self) -> int:
        return len(self.tags)

    @typechecked
    def __iter__(self):
        return iter(self.tags)
