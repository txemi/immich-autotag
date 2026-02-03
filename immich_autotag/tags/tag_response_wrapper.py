import attrs

from immich_autotag.api.logging_proxy.types import TagResponseDto
from immich_autotag.types.uuid_wrappers import TagUUID


@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.
    """

    _tag: TagResponseDto = attrs.field(
        validator=attrs.validators.instance_of(TagResponseDto)
    )

    def get_id(self) -> TagUUID:
        id_val = self._tag.id
        return TagUUID.from_string(id_val)

    def get_name(self) -> str:
        return self._tag.name

    def name(self) -> str:
        return self.get_name()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TagWrapper):
            return self.get_id() == other.get_id()
        return False

    def __str__(self) -> str:
        return f"TagWrapper(id={self.get_id()}, name={self.get_name()})"
