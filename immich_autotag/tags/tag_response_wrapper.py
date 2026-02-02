import attrs
from typeguard import typechecked

from immich_autotag.api.immich_proxy.types import TagResponseDto
from immich_autotag.types.uuid_wrappers import TagUUID


@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.
    """

    _tag: TagResponseDto = attrs.field(
        validator=attrs.validators.instance_of(TagResponseDto)
    )

    @typechecked
    def get_id(self) -> TagUUID:
        id_val = self._tag.id
        return TagUUID.from_string(id_val)

    @typechecked
    def get_name(self) -> str:
        return self._tag.name

    def to_dto(self) -> TagResponseDto:
        return self._tag

    def __eq__(self, other) -> bool:
        if isinstance(other, TagWrapper):
            return self.get_id() == other.get_id()
        return False

    def __str__(self) -> str:
        return f"TagWrapper(id={self.get_id()}, name={self.get_name()})"
