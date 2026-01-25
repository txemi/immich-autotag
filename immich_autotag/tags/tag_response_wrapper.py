import attrs
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.
    """

    tag: TagResponseDto

    @typechecked
    def get_id(self) -> "UUID":
        from uuid import UUID

        id_val = self.tag.id
        return UUID(id_val)

    @typechecked
    def get_name(self) -> str:
        return self.tag.name

    def to_dto(self) -> TagResponseDto:
        return self.tag

    def __eq__(self, other) -> bool:
        if isinstance(other, TagWrapper):
            return self.get_id() == other.get_id()
        return False

    def __str__(self) -> str:
        return f"TagWrapper(id={self.get_id()}, name={self.get_name()})"
