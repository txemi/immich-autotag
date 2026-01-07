import attrs
from immich_client.models.tag_response_dto import TagResponseDto
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper for TagResponseDto that allows adding useful methods and properties.
    """

    tag: TagResponseDto

    @property
    def id(self) -> str:
        return self.tag.id

    @property
    def name(self) -> str:
        return self.tag.name

    def __str__(self) -> str:
        return f"TagWrapper(id={self.id}, name={self.name})"

    def __eq__(self, other) -> bool:
        if isinstance(other, TagWrapper):
            return self.id == other.id
        return False

    def to_dto(self) -> TagResponseDto:
        return self.tag

    @typechecked
    def get_name(self) -> str:
        """
        Returns the tag name in a robust and encapsulated manner.
        """
        return self.name
