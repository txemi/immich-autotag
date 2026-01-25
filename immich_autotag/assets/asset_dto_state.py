import enum
from datetime import datetime
from typing import Iterator
from uuid import UUID

import attrs
from immich_client.types import Unset

from immich_autotag.api.immich_proxy.assets import AssetResponseDto


class AssetDtoType(enum.Enum):
    PARTIAL = "partial"
    FULL = "full"


# Exception for tags not loaded
class TagsNotLoadedError(Exception):
    pass


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

    def update(self, *, dto: AssetResponseDto, type_: AssetDtoType) -> None:
        self._dto = dto
        self._type = type_
        self._loaded_at = datetime.now()

    def get_tags(self):
        """
        Returns a list of TagWrapper for the tags associated with this asset.
        If tag_collection is provided, returns TagWrapper objects; otherwise, uses the singleton collection (requires it to be initialized, or pass client for first use).
        If neither is available, returns raw tag DTOs.
        Raises TagsNotLoadedError if tags are not loaded (UNSET).
        """
        tags = self._dto.tags
        if isinstance(tags, Unset):
            raise TagsNotLoadedError(
                "Tags are UNSET; tags have not been loaded for this asset."
            )
        if tags is None:
            raise TagsNotLoadedError(
                "Tags are None; this should not happen with DTOs. Please check DTO construction."
            )
        from immich_autotag.context.immich_context import ImmichContext

        tag_collection = ImmichContext.get_default_instance().get_tag_collection()
        wrappers = []
        for tag in tags:
            wrapper = tag_collection.find_by_name(tag.name)
            if wrapper is None:

                raise ValueError(
                    f"Tag '{tag.name}' not found in TagCollectionWrapper for asset {self._dto.id}"
                )
            wrappers.append(wrapper)
        return wrappers

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
        return any(tag.name and tag.name.lower() == tag_name.lower() for tag in tags)

    def get_uuid(self) -> UUID:
        return UUID(self._dto.id)

    def get_original_file_name(self) -> str:
        return self._dto.original_file_name
