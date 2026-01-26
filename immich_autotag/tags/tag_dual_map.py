from typing import TYPE_CHECKING, Any, List

import attrs
from typeguard import typechecked

from immich_autotag.tags.tag_id_map import TagIdMap
from immich_autotag.tags.tag_name_map import TagNameMap

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper


@attrs.define(auto_attribs=True, slots=True)
class TagDualMap:
    """
    Encapsulates TagIdMap (by id) and TagNameMap (by name).
    Keeps both in sync and provides efficient access.
    """

    _id_map: TagIdMap = attrs.field(factory=TagIdMap)
    _name_map: TagNameMap = attrs.field(factory=TagNameMap)

    @typechecked
    def add(self, tag: "TagWrapper"):
        self._id_map.append(tag)
        self._name_map.add(tag)

    @typechecked
    def remove(self, tag: "TagWrapper"):
        self._id_map.remove(tag)
        self._name_map.remove(tag)

    @typechecked
    def get_by_id(self, tag_id: Any) -> "TagWrapper":
        return self._id_map.get_by_id(tag_id)

    @typechecked
    def get_by_name(self, name: str) -> "TagWrapper":
        return self._name_map.get(name)

    def values(self) -> List["TagWrapper"]:
        # Returns all TagWrapper objects
        return self._id_map.to_list()

    def clear(self):
        self._id_map._id_to_tag.clear()
        self._name_map._name_to_tag.clear()

    def __len__(self):
        return len(self._id_map._id_to_tag)

    def __iter__(self):
        return iter(self._id_map._id_to_tag.values())
