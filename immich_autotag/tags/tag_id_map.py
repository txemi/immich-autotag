from typing import TYPE_CHECKING, Dict, List
from uuid import UUID

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper


@attrs.define(auto_attribs=True, slots=True)
class TagIdMap:
    """
    Mapa eficiente de id (UUID o str) a TagWrapper.
    """

    _id_to_tag: Dict[UUID, "TagWrapper"] = attrs.field(factory=dict)

    @typechecked
    def append(self, tag: "TagWrapper"):
        tag_id = tag.get_id()
        if tag_id in self._id_to_tag:
            raise ValueError(f"Tag con id {tag_id} ya existe en TagIdMap")
        self._id_to_tag[tag_id] = tag

    @typechecked
    def remove(self, tag: "TagWrapper"):
        tag_id = tag.get_id()
        if tag_id in self._id_to_tag:
            del self._id_to_tag[tag_id]
        else:
            raise ValueError(f"Tag con id {tag_id} no encontrada en TagIdMap")

    @typechecked
    def get_by_id(self, tag_id: UUID) -> "TagWrapper":
        if tag_id not in self._id_to_tag:
            raise RuntimeError(f"Tag con id {tag_id} no existe en TagIdMap")
        return self._id_to_tag[tag_id]

    def to_list(self) -> List["TagWrapper"]:
        return list(self._id_to_tag.values())
