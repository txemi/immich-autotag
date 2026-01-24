import enum
from datetime import datetime
from typing import Iterator

import attrs

from immich_autotag.api.immich_proxy.assets import AssetResponseDto
from immich_autotag.api.immich_proxy.tags import TagResponseDto


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
    def type(self) -> AssetDtoType:
        return self._type

    @property
    def loaded_at(self) -> datetime:
        return self._loaded_at

    def update(self, dto: AssetResponseDto, type_: AssetDtoType) -> None:
        self._dto = dto
        self._type = type_
        self._loaded_at = datetime.now()

    def get_tags(self):
        # Placeholder: implement actual tag extraction from self._dto if available
        raise NotImplementedError("get_tags method not implemented yet")

    def get_dates(self):
        def _get_dates(asset__: AssetResponseDto) -> Iterator[datetime]:
            yield asset__.created_at
            yield asset__.file_created_at
            yield asset__.file_modified_at
            yield asset__.local_date_time

        date_candidates = list(_get_dates(self._dto))
        return date_candidates

    def has_tag(self, tag_name: str) -> bool:
        if self._type == AssetDtoType.PARTIAL:
            raise NotImplementedError(
                "has_tag not implemented for PARTIAL AssetDtoType"
            )
        from immich_client.types import Unset  # TODO: Move Unset to proxy if needed

        tags = self._dto.tags
        if isinstance(tags, Unset):
            raise NotImplementedError("Tags are UNSET; cannot check for tag existence.")
        # Aseguramos el tipo para el editor y mypy
        from typing import cast

        tags = cast(list[TagResponseDto], tags)
        return any(tag.name and tag.name.lower() == tag_name.lower() for tag in tags)
