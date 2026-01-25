from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

import attrs
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked

from immich_autotag.tags.tag_dual_map import TagDualMap
from immich_autotag.types import ImmichClient

_tag_collection_singleton: "TagCollectionWrapper | None" = None


@attrs.define(auto_attribs=True, slots=True)
class TagCollectionWrapper:
    _index: TagDualMap = attrs.field(factory=TagDualMap)

    def __attrs_post_init__(self):
        global _tag_collection_singleton
        if (
            _tag_collection_singleton is not None
            and self is not _tag_collection_singleton
        ):
            raise RuntimeError(
                "TagCollectionWrapper singleton already exists. Use TagCollectionWrapper.get_instance()."
            )

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

        refreshed = self.__class__._from_api()
        self._index.clear()
        for tag in refreshed._index.values():
            self._index.add(tag)

    @typechecked
    def create_tag_if_not_exists(
        self, *, name: str, client: ImmichClient
    ) -> "TagWrapper":
        """
        Creates the tag in Immich if it doesn't exist and adds it to the local collection.
        Returns the corresponding TagResponseDto.
        """
        tag = self.find_by_name(name)
        if tag is not None:
            return tag

        from immich_client import errors as immich_errors

        from immich_autotag.api.immich_proxy.tags import proxy_create_tag

        try:
            new_tag_dto = proxy_create_tag(client=client, name=name)
            if new_tag_dto is None:
                raise ValueError("API returned None for new tag creation")
            new_tag = TagWrapper(new_tag_dto)
            self._index.add(new_tag)
            return new_tag
        except immich_errors.UnexpectedStatus as e:
            if e.status_code == 400 and "already exists" in str(e):
                self._sync_from_api(client)
                tag = self.find_by_name(name)
                if tag is not None:
                    return tag
            raise

    @staticmethod
    @typechecked
    def _from_api() -> "TagCollectionWrapper":
        """
        Builds a TagCollectionWrapper instance by fetching tags from the Immich API.
        Uses the client from ImmichContext singleton.
        """
        from immich_autotag.api.immich_proxy.tags import proxy_get_all_tags
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.tags.tag_response_wrapper import TagWrapper

        client_wrapper = ImmichClientWrapper.get_default_instance()
        client = client_wrapper.get_client()
        tags_dto = proxy_get_all_tags(client=client)
        if tags_dto is None:
            tags_dto = []
        tags = [TagWrapper(tag) for tag in tags_dto]
        wrapper = TagCollectionWrapper()
        wrapper._index.clear()
        for tag in tags:
            wrapper._index.add(tag)
        return wrapper

    @typechecked
    def find_by_name(self, name: str) -> "TagWrapper | None":
        return self._index.get_by_name(name)

    @typechecked
    def find_by_id(self, id_: "UUID") -> "TagWrapper | None":
        return self._index.get_by_id(id_)

    @typechecked
    def __iter__(self):
        return iter(self._index)

    @typechecked
    def __contains__(self, name: str) -> bool:
        return self.find_by_name(name) is not None

    @typechecked
    def __len__(self) -> int:
        return len(self._index)

    @classmethod
    def get_instance(cls) -> "TagCollectionWrapper":
        """
        Returns the singleton instance of TagCollectionWrapper. If not initialized, fetches from API using the client from ImmichContext singleton.
        """
        global _tag_collection_singleton
        if _tag_collection_singleton is not None:
            return _tag_collection_singleton
        _tag_collection_singleton = cls._from_api()
        return _tag_collection_singleton

    def get_tag_from_dto(self, dto: "TagResponseDto") -> "TagWrapper | None":
        """
        Devuelve el TagWrapper correspondiente a un TagResponseDto (dto), o None si no existe.
        """
        tag = self.find_by_id(UUID(dto.id))
        if tag is not None:
            return tag
        name = dto.name
        return self.find_by_name(name)
        raise NotImplementedError(
            "TagResponseDto no tiene ni id ni name válidos para buscar el TagWrapper."
        )
