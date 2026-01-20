import attrs
from typeguard import typechecked

from immich_autotag.tags.tag_response_wrapper import TagWrapper
from immich_autotag.types import ImmichClient


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
        from immich_client.errors import UnexpectedStatus
        from immich_client.models.tag_create_dto import TagCreateDto

        tag_create = TagCreateDto(name=name)
        try:
            new_tag_dto = create_tag.sync(client=client, body=tag_create)
            new_tag = TagWrapper(new_tag_dto)
            self.tags.append(new_tag)
            return new_tag
        except UnexpectedStatus as e:
            if e.status_code == 400 and "already exists" in str(e):
                # Cache is out of sync - tag exists on server but not in our cache
                # Refresh from API to get the actual tag
                self._sync_from_api(client)
                tag = self.find_by_name(name)
                if tag is not None:
                    return tag
            # If it's a different error, re-raise
            raise

    @typechecked
    def _sync_from_api(self, client: ImmichClient) -> None:
        """
        Refresh tag cache from the API to handle external changes or race conditions.
        This indicates a cache desynchronization that should be investigated.
        """
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            "[TAG_CACHE] Detected out-of-sync tag cache, refreshing from API"
        )

        refreshed = self.from_api(client)
        self.tags = refreshed.tags

    @staticmethod
    @typechecked
    def from_api(client: ImmichClient) -> "TagCollectionWrapper":
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
