from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.types.uuid_wrappers import TagUUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

import attrs
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked

from immich_autotag.tags.tag_dual_map import TagDualMap
from immich_autotag.types.client_types import ImmichClient

_tag_collection_singleton: "TagCollectionWrapper | None" = None


class TagCollectionWrapperLoadError(Exception):
    pass


@attrs.define(auto_attribs=True, slots=True)
class TagCollectionWrapper:

    _index: TagDualMap = attrs.field(factory=TagDualMap)
    _fully_loaded: bool = attrs.field(default=False, init=False)

    def __attrs_post_init__(self):
        global _tag_collection_singleton
        if (
            _tag_collection_singleton is not None
            and self is not _tag_collection_singleton
        ):
            raise RuntimeError(
                "TagCollectionWrapper singleton already exists. Use TagCollectionWrapper.get_instance()."
            )

    def _set_fully_loaded(self):
        self._fully_loaded = True

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

        self._fully_loaded = False
        self._load_all_from_api()

    def _load_single_by_id_from_api(self, id_: TagUUID):
        """
        Fetch a tag by id using the efficient proxy and add it to the index if found.
        Returns the found TagWrapper or None.
        """

        from immich_autotag.api.immich_proxy.tags import proxy_get_tag_by_id
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.tags.tag_response_wrapper import TagWrapper

        client_wrapper = ImmichClientWrapper.get_default_instance()
        client = client_wrapper.get_client()
        try:
            tag_dto = proxy_get_tag_by_id(client=client, tag_id=id_)
        except Exception:
            tag_dto = None
        if tag_dto is not None:
            tag_obj = TagWrapper(tag_dto)
            self._index.add(tag_obj)
            return tag_obj
        return None

    def _load_single_by_name_from_api(self, name: str):
        """
        Centralizes full loading: if not fully_loaded, loads all tags and searches in the index.
        This avoids duplication and keeps the logic in one place.
        """
        if not self._fully_loaded:
            self._load_all_from_api()
        return self._index.get_by_name(name)

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
            from immich_autotag.tags.tag_response_wrapper import TagWrapper

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

    def _load_all_from_api(self):
        """
        Loads all tags from the API and adds them to the index, marking as fully_loaded.
        If already fully_loaded, does nothing.
        """
        if self._fully_loaded:
            return
        from immich_autotag.api.immich_proxy.tags import proxy_get_all_tags
        from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
        from immich_autotag.tags.tag_response_wrapper import TagWrapper

        client_wrapper = ImmichClientWrapper.get_default_instance()
        client = client_wrapper.get_client()
        tags_dto = proxy_get_all_tags(client=client)
        if tags_dto is None:
            raise RuntimeError("API returned None when fetching all tags")
        self._index.clear()
        for tag_dto in tags_dto:
            tag = TagWrapper(tag_dto)
            self._index.add(tag)
        self._set_fully_loaded()

    @staticmethod
    @typechecked
    def _from_api() -> "TagCollectionWrapper":
        """
        Builds a TagCollectionWrapper instance by fetching tags from the Immich API.
        Uses the client from ImmichContext singleton.
        """
        wrapper = TagCollectionWrapper()
        wrapper._load_all_from_api()
        return wrapper

    @typechecked
    def find_by_name(self, name: str) -> "TagWrapper | None":
        try:
            tag = self._index.get_by_name(name)
            return tag
        except Exception:
            pass
        # Lazy-load individual tag if not fully_loaded
        if not self._fully_loaded:
            return self._load_single_by_name_from_api(name)
        return None

    @typechecked
    def find_by_id(self, id_: "TagUUID") -> "TagWrapper | None":
        try:
            tag = self._index.get_by_id(id_)
            return tag
        except Exception:
            pass
        # Lazy-load individual tag if not fully_loaded
        if not self._fully_loaded:
            return self._load_single_by_id_from_api(id_)
        return None

    @typechecked
    def __iter__(self):
        # If not fully_loaded, force full loading
        if not self._fully_loaded:
            self._load_all_from_api()
        return iter(self._index)

    @typechecked
    def __contains__(self, name: str) -> bool:
        return self.find_by_name(name) is not None

    @typechecked
    def __len__(self) -> int:
        # If not fully_loaded, force full loading
        if not self._fully_loaded:
            self._load_all_from_api()
        return len(self._index)

    @classmethod
    def get_instance(cls) -> "TagCollectionWrapper":
        """
        Returns the singleton instance of TagCollectionWrapper. If not initialized,
        creates it empty (without loading tags). Full loading is done on demand.
        """
        global _tag_collection_singleton
        if _tag_collection_singleton is not None:
            return _tag_collection_singleton
        _tag_collection_singleton = TagCollectionWrapper()
        return _tag_collection_singleton

    def get_tag_from_dto(self, dto: "TagResponseDto") -> "TagWrapper | None":
        """
        Returns the TagWrapper corresponding to a TagResponseDto (dto), or None if it
        does not exist.
        """
        from immich_autotag.types.uuid_wrappers import TagUUID

        tag_id = TagUUID.from_string(dto.id)
        tag = self.find_by_id(tag_id)
        if tag is not None:
            return tag
        name = dto.name
        return self.find_by_name(name)

    @staticmethod
    def maintenance_delete_conflict_tags(client: ImmichClient) -> int:
        """
        MAINTENANCE HACK: Deletes all tags whose name starts with the fixed conflict prefix.
        Returns the number of deleted tags.
        """
        from immich_autotag.config.manager import ConfigManager

        conf = ConfigManager.get_instance().get_config()
        prefixes = [
            conf.duplicate_processing.autotag_album_conflict,
            conf.duplicate_processing.autotag_classification_conflict_prefix,
        ]
        prefixes = [p for p in prefixes if p]
        from immich_autotag.api.immich_proxy.tags import (
            proxy_delete_tag,
            proxy_get_all_tags,
        )

        tags_dto = proxy_get_all_tags(client=client) or []
        count = 0
        from immich_autotag.types.uuid_wrappers import TagUUID

        for tag in tags_dto:
            if any(tag.name.startswith(prefix) for prefix in prefixes):
                proxy_delete_tag(client=client, tag_id=TagUUID.from_string(tag.id))
                print(f"[CLEANUP] Deleted tag: {tag.name} (id={tag.id})")
                count += 1
        return count
