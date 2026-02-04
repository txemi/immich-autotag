from typing import TYPE_CHECKING, Dict, List

import attrs
from typeguard import typechecked

from immich_autotag.types.uuid_wrappers import TagUUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper


@attrs.define(auto_attribs=True, slots=True)
class TagIdMap:
    """
    Mapa eficiente de id (UUID o str) a TagWrapper.
    """

    _id_to_tag: Dict[TagUUID, "TagWrapper"] = attrs.field(
        factory=dict,
        repr=lambda value: f"size={len(value)}",
    )

    @typechecked
    def append(self, tag: "TagWrapper"):
        tag_id = tag.get_id()
        if tag_id in self._id_to_tag:
            raise ValueError(f"Tag with id {tag_id} already exists in TagIdMap")
        self._id_to_tag[tag_id] = tag

    @typechecked
    def remove(self, tag: "TagWrapper"):
        tag_id = tag.get_id()
        if tag_id in self._id_to_tag:
            del self._id_to_tag[tag_id]
        else:
            raise ValueError(f"Tag with id {tag_id} not found in TagIdMap")

    @typechecked
    def get_by_id(self, tag_id: TagUUID) -> "TagWrapper":
        if tag_id not in self._id_to_tag:
            raise RuntimeError(f"Tag with id {tag_id} does not exist in TagIdMap")
        return self._id_to_tag[tag_id]

    def to_list(self) -> List["TagWrapper"]:
        return list(self._id_to_tag.values())

    @typechecked
    def clear(self):
        """
        Remove all elements from the ID map.
        """
        self._id_to_tag.clear()
