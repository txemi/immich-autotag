from typing import Dict, TYPE_CHECKING, List
import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

@attrs.define(auto_attribs=True, slots=True)
class TagNameMap:
    """
    Mapa eficiente de nombre (str) a TagWrapper.
    """
    _name_to_tag: Dict[str, 'TagWrapper'] = attrs.field(factory=dict)

    @typechecked
    def add(self, tag: 'TagWrapper'):
        name = tag.name
        if name in self._name_to_tag:
            raise RuntimeError(f"Tag con nombre '{name}' ya existe en TagNameMap.")
        self._name_to_tag[name] = tag

    @typechecked
    def remove(self, tag: 'TagWrapper'):
        name = tag.name
        if name not in self._name_to_tag:
            raise RuntimeError(f"No existe tag con nombre '{name}' en TagNameMap.")
        del self._name_to_tag[name]

    @typechecked
    def get(self, name: str) -> 'TagWrapper':
        if name not in self._name_to_tag:
            raise RuntimeError(f"Tag con nombre '{name}' no existe en TagNameMap.")
        return self._name_to_tag[name]

    def to_list(self) -> List['TagWrapper']:
        return list(self._name_to_tag.values())
