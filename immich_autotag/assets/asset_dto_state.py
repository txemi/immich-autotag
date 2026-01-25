import enum
from datetime import datetime
from typing import Iterator
from uuid import UUID

import attrs
from immich_client.types import Unset

from immich_autotag.api.immich_proxy.assets import AssetResponseDto


class AssetDtoType(enum.Enum):
    """
    Encodes which API endpoint was used to load the Asset DTO.
    - PARTIAL: Loaded via a bulk search endpoint (e.g., /assets/search), typically with incomplete or partial data.
    - FULL: Loaded via a single-asset detail endpoint (e.g., /assets/{id}), with all fields populated.
    This distinction is important for knowing whether the DTO contains all available data or only a subset.
    """

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
    # Indicates which API endpoint was used to load this DTO (e.g., 'search' for bulk/partial, 'get_by_id' for full detail).
    # This allows consumers to know if the DTO contains all fields (FULL) or only a subset (PARTIAL).
    # See AssetDtoType for details.
    _api_endpoint_source: AssetDtoType
    _loaded_at: datetime = attrs.field(factory=datetime.now)

    def __attrs_post_init__(self):
        # Comprobación defensiva del tipo de tags según el endpoint de la API usado
        tags = getattr(self._dto, "tags", None)
        if self._api_endpoint_source == AssetDtoType.FULL:
            if (
                tags is not None
                and not isinstance(tags, list)
                and not isinstance(tags, Unset)
            ):
                raise TypeError(
                    f"En modo FULL, tags debe ser una lista o Unset, pero es {type(tags)}"
                )
        elif self._api_endpoint_source == AssetDtoType.PARTIAL:
            if (
                tags is not None
                and not isinstance(tags, set)
                and not isinstance(tags, Unset)
            ):
                raise TypeError(
                    f"En modo PARTIAL, tags debe ser un set o Unset, pero es {type(tags)}"
                )
        # Si se amplían los tipos, añadir más comprobaciones aquí

    def get_type(self) -> AssetDtoType:
        return self._api_endpoint_source

    def get_loaded_at(self) -> datetime:
        return self._loaded_at

    def update(
        self, *, dto: AssetResponseDto, api_endpoint_source: AssetDtoType
    ) -> None:
        self._dto = dto
        self._api_endpoint_source = api_endpoint_source
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

    def to_cache_dict(self) -> dict:
        """
        Serializes the state to a dictionary, including loaded_at in ISO format.
        """
        return {
            "dto": self._dto.to_dict() if hasattr(self._dto, "to_dict") else self._dto,
            "type": self._api_endpoint_source.value,
            "loaded_at": self._loaded_at.isoformat(),
        }

    @classmethod
    def from_cache_dict(cls, data: dict) -> "AssetDtoState":
        """
        Reconstruye el estado desde un diccionario serializado.
        """
        from immich_client.models.asset_response_dto import AssetResponseDto

        dto = AssetResponseDto.from_dict(data["dto"])
        api_endpoint_source = AssetDtoType(data["type"])
        loaded_at = datetime.fromisoformat(data["loaded_at"])
        return cls(
            _dto=dto, _api_endpoint_source=api_endpoint_source, _loaded_at=loaded_at
        )
