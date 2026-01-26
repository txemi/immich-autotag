from typing import TYPE_CHECKING, Dict, List

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper


@attrs.define(auto_attribs=True, slots=True)
class TagNameMap:
    """
    Efficient map from name (str) to TagWrapper.
    """

    _name_to_tag: Dict[str, "TagWrapper"] = attrs.field(factory=dict)

    @typechecked
    def add(self, tag: "TagWrapper"):
        name = tag.get_name()
        if name in self._name_to_tag:
            raise RuntimeError(f"Tag with name '{name}' already exists in TagNameMap.")
        self._name_to_tag[name] = tag

    @typechecked
    def remove(self, tag: "TagWrapper"):
        name = tag.get_name()
        if name not in self._name_to_tag:
            raise RuntimeError(f"No tag with name '{name}' exists in TagNameMap.")
        del self._name_to_tag[name]

    @typechecked
    def get(self, name: str) -> "TagWrapper":
        if name not in self._name_to_tag:
            raise RuntimeError(f"Tag with name '{name}' does not exist in TagNameMap.")
        return self._name_to_tag[name]

    def to_list(self) -> List["TagWrapper"]:
        return list(self._name_to_tag.values())
