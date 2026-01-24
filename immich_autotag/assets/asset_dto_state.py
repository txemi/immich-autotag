import enum
from datetime import datetime

import attrs
from immich_client.models.asset_response_dto import AssetResponseDto


class AssetDtoType(enum.Enum):
    PARTIAL = "partial"
    FULL = "full"


@attrs.define(auto_attribs=True, slots=True)
class AssetDtoState:
    """
    Encapsulates the current DTO, its type (partial/full), and the loaded_at timestamp.
    This class never performs API calls or business logic—just holds and exposes data.
    """

    _dto: AssetResponseDto
    _type: AssetDtoType
    _loaded_at: datetime = attrs.field(factory=datetime.now)

    @property
    def dto(self) -> AssetResponseDto:
        return self._dto

    @property
    def type(self) -> AssetDtoType:
        return self._type

    @property
    def loaded_at(self) -> datetime:
        return self._loaded_at

    def update(self, dto: AssetResponseDto, type_: AssetDtoType) -> None:
        self._dto = dto
        self._type = type_
        self._loaded_at = datetime.now()
