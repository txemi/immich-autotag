import attrs
from immich_client.models.tag_response_dto import TagResponseDto

@attrs.define(auto_attribs=True, slots=True)
class TagWrapper:
    """
    Wrapper para TagResponseDto que permite añadir métodos y propiedades útiles.
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
