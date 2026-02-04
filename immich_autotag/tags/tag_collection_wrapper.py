from __future__ import annotations

from typing import TYPE_CHECKING

from immich_autotag.types.uuid_wrappers import TagUUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

    # (Removed duplicate unused imports to fix Flake8)

import attrs
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
    from immich_autotag.report.modification_entry import ModificationEntry

    def __attrs_post_init__(self):
        if (
            _tag_collection_singleton is not None
            and self is not _tag_collection_singleton
        ):
            raise RuntimeError(
                "TagCollectionWrapper singleton already exists. Use "
                "TagCollectionWrapper.get_instance()."
            )

    def _set_fully_loaded(self):
        self._fully_loaded = True

    def _load_all_from_api(self):
        """
        Loads all tags from the API and adds them to the index, marking as fully_loaded.
        If already fully_loaded, does nothing.
        """
        if self._fully_loaded:
            return
        from immich_autotag.api.logging_proxy.load_all_tags_wrapped import (
            load_all_tags_wrapped,
        )

        self._index.clear()
        for tag in load_all_tags_wrapped():
            self._index.add(tag)
        self._set_fully_loaded()

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

    def _load_single_by_id_from_api(self, id_: "TagUUID") -> "TagWrapper | None":
        """
        Fetch a tag by id using the efficient proxy and add it to the index if found.
        Returns the found TagWrapper or None.
        """
        from immich_autotag.api.logging_proxy.load_tag_by_id_wrapped import (
            load_tag_by_id_wrapped,
        )

        tag_obj = load_tag_by_id_wrapped(id_)
        if tag_obj is not None:
            self._index.add(tag_obj)
            return tag_obj
        return None

    def _load_single_by_name_from_api(self, name: str):
        """
        Centralizes full loading: if not fully_loaded, loads all tags and
        searches in the index. This avoids duplication and keeps the logic in
        one place.
        """
        if not self._fully_loaded:
            self._load_all_from_api()
        return self._index.get_by_name(name)

    @typechecked
    def create_tag_if_not_exists(
        self, *, name: str, client: ImmichClient
    ) -> "TagWrapper":
        """
        Creates the tag in Immich if it doesn't exist and adds it to the local
        collection. Returns the corresponding TagResponseDto.
        """

        tag = self.find_by_name(name)
        if tag is not None:
            return tag

        from immich_autotag.api.logging_proxy.tags import logging_create_tag
        from immich_autotag.api.logging_proxy.types import immich_errors

        try:
            # logging_create_tag returns ModificationEntry containing the TagWrapper
            entry = logging_create_tag(client=client, name=name)
            new_tag = entry.tag
            if new_tag is None:
                raise RuntimeError(
                    f"Tag creation succeeded but entry has no tag: {name}"
                )
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
            tag_obj = self._index.get_by_id(id_)
            return tag_obj
        except Exception:
            pass
        # Lazy-load individual tag if not fully_loaded
        if not self._fully_loaded:
            return self._load_single_by_id_from_api(id_)
        return None

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

    def _find_candidate_tag(self, new_tag: "TagWrapper") -> "TagWrapper | None":
        """
        INTERNAL: Helper for merging external tag entities.

        This method is NOT for general use. It is designed to assist in merging a tag entity
        (typically from an external payload) into the local collection, by searching for a candidate
        tag in the collection using both ID and name.

        - If both ID and name are found and refer to different tags, raises an exception (conflict).
        - If only one is found, returns that candidate.
        - If neither is found, returns None.

        This logic is intentionally strict and is only suitable for controlled merge/update scenarios.
        It is not recommended for general lookup or business logic.
        """
        tag_id = new_tag.get_id()
        by_id = self.find_by_id(tag_id)
        name = new_tag.get_name()
        by_name = self.find_by_name(name)
        if by_id and by_name:
            if by_id != by_name:
                raise RuntimeError(
                    f"TagCollectionWrapper: Conflicting tags found for id={tag_id} and name={name}"
                )
            return by_id
        if by_id:
            return by_id
        if by_name:
            return by_name
        return None

    def merge_or_update_tag(self, new_tag: "TagWrapper") -> "TagWrapper | None":
        """
        Receives a new TagWrapper and compares it with the candidate in the collection (by id/name).
        If no candidate is found, adds the new tag and returns it.
        If a candidate exists, calls get_best_tag and updates the map if needed.
        """
        candidate = self._find_candidate_tag(new_tag)
        if candidate is None:
            self._index.add(new_tag)
            return new_tag
        best_tag = candidate.get_best_tag(new_tag)
        if best_tag is candidate:
            return candidate
        self._index.add(best_tag)
        return best_tag

    @staticmethod
    def maintenance_delete_conflict_tags(client: ImmichClient) -> int:
        """
        MAINTENANCE HACK: Deletes all tags whose name starts with any conflict prefix.
        Returns the number of deleted tags.
        """
        from immich_autotag.api.logging_proxy.load_all_tags_wrapped import (
            load_all_tags_wrapped,
        )
        from immich_autotag.api.logging_proxy.tags import logging_delete_tag

        tags_wrapped = load_all_tags_wrapped()
        count = 0
        for tag_wrapper in tags_wrapped:
            if tag_wrapper.has_conflict_prefix():
                logging_delete_tag(
                    client=client,
                    tag=tag_wrapper,
                    reason="maintenance_cleanup",
                )
                count += 1
        return count

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
