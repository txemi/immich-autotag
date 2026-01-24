import attrs
from typeguard import typechecked

from immich_autotag.tags.tag_response_wrapper import TagWrapper
from immich_autotag.types import ImmichClient


@attrs.define(auto_attribs=True, slots=True)
class TagCollectionWrapper:
    tags: list[TagWrapper] = attrs.field(
        factory=list, validator=attrs.validators.instance_of(list)
    )

    def __attrs_post_init__(self):
        # Defensive: never allow None for tags
        if self.tags is None:
            raise ValueError("tags cannot be None; use an empty list instead")

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

    @typechecked
    def create_tag_if_not_exists(self, name: str, client) -> TagWrapper:
        """
        Creates the tag in Immich if it doesn't exist and adds it to the local collection.
        Returns the corresponding TagResponseDto.
        """
        tag = self.find_by_name(name)
        if tag is not None:
            return tag
        from immich_autotag.api.immich_proxy.tags import (
            UnexpectedStatus,
            proxy_create_tag,
        )

        try:
            new_tag_dto = proxy_create_tag(client=client, name=name)
            if new_tag_dto is None:
                raise ValueError("API returned None for new tag creation")
            new_tag = TagWrapper(new_tag_dto)
            self.tags.append(new_tag)
            return new_tag
        except UnexpectedStatus as e:
            if e.status_code == 400 and "already exists" in str(e):
                self._sync_from_api(client)
                tag = self.find_by_name(name)
                if tag is not None:
                    return tag
            raise

    @staticmethod
    @typechecked
    def from_api(client: ImmichClient) -> "TagCollectionWrapper":
        """
        Builds a TagCollectionWrapper instance by fetching tags from the Immich API.
        """
        from immich_autotag.api.immich_proxy.tags import proxy_get_all_tags

        tags_dto = proxy_get_all_tags(client=client)
        if tags_dto is None:
            tags_dto = []
        tags = [TagWrapper(tag) for tag in tags_dto]
        return TagCollectionWrapper(tags=tags)

    @typechecked
    def find_by_name(self, name: str) -> TagWrapper | None:
        for tag in self.tags:
            if tag.name == name:
                return tag
        return None

    @typechecked
    def __iter__(self):
        return iter(self.tags)

    @typechecked
    def __contains__(self, name: str) -> bool:
        return any(tag.name == name for tag in self.tags)

    @typechecked
    def __len__(self) -> int:
        return len(self.tags)
