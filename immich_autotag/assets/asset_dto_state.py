from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from immich_autotag.types.uuid_wrappers import AssetUUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

import enum
from datetime import datetime
from typing import Any, Iterator, Mapping, cast
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

    FULL = "full"
    SEARCH = "search"
    ALBUM = "album"


# Exception for tags not loaded
class TagsNotLoadedError(Exception):
    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetDtoState:
    from typing import Any, Mapping, cast

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
        # Defensive check of the type of tags according to the API endpoint used
        tags = getattr(self._dto, "tags", None)
        if self._api_endpoint_source == AssetDtoType.FULL:
            if (
                tags is not None
                and not isinstance(tags, list)
                and not isinstance(tags, Unset)
            ):
                raise TypeError(
                    f"In FULL mode, tags must be a list or Unset, but it is {type(tags)}"
                )
        else:
            if (
                tags is not None
                and not isinstance(tags, set)
                and not isinstance(tags, Unset)
            ):
                raise TypeError(
                    f"En modo PARTIAL, tags debe ser un set o Unset, pero es {type(tags)}"
                )
        # If more types are added, add more checks here

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

    def get_tags(self) -> list["TagWrapper"]:
        """
        Returns a list of TagWrapper for the tags associated with this asset.
        If tag_collection is provided, returns TagWrapper objects; otherwise, uses the singleton collection (requires it to be initialized, or pass client for first use).
        If neither is available, returns raw tag DTOs.
        Raises TagsNotLoadedError if tags are not loaded (UNSET).
        """

        full = self.get_self_if_full()
        tags = full._dto.tags
        if isinstance(tags, Unset):
            raise TagsNotLoadedError(
                "Tags are UNSET; tags have not been loaded for this asset."
            )
        from immich_autotag.context.immich_context import ImmichContext

        tag_collection = ImmichContext.get_default_instance().get_tag_collection()
        wrappers: list["TagWrapper"] = []
        for tag in tags:
            wrapper = tag_collection.get_tag_from_dto(tag)
            if wrapper is not None:
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
        """
        Returns True if the asset has a tag with that name (case-insensitive), False otherwise.
        """
        tag_names = self.get_tag_names()
        return any(tn.lower() == tag_name.lower() for tn in tag_names)

    def get_uuid(self) -> AssetUUID:
        return AssetUUID(self._dto.id)

    def get_original_file_name(self) -> Path:
        return Path(self._dto.original_file_name)

    def to_cache_dict(self) -> dict[str, object]:
        """
        Serializes the state to a dictionary, including loaded_at in ISO format.
        """
        return {
            "dto": self._dto.to_dict() if hasattr(self._dto, "to_dict") else self._dto,
            "type": self._api_endpoint_source.value,
            "loaded_at": self._loaded_at.isoformat(),
        }

    @classmethod
    def _from_dto(cls, dto, api_endpoint_source, loaded_at):
        return cls(
            dto=dto, api_endpoint_source=api_endpoint_source, loaded_at=loaded_at
        )

    @classmethod
    def from_cache_dict(cls, data: dict[str, object]) -> "AssetDtoState":
        """
        Reconstructs the state from a serialized dictionary.
        """
        from immich_client.models.asset_response_dto import AssetResponseDto

        dto = AssetResponseDto.from_dict(cast(Mapping[str, Any], data["dto"]))
        api_endpoint_source = AssetDtoType(str(data["type"]))
        loaded_at = datetime.fromisoformat(str(data["loaded_at"]))

        return cls._from_dto(
            dto=dto, api_endpoint_source=api_endpoint_source, loaded_at=loaded_at
        )

    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset, or an empty list if there are no tags.
        """
        tag_wrappers = self.get_tags()
        return [tag_wrapper.get_name() for tag_wrapper in tag_wrappers]

    def get_self_if_full(self) -> "AssetDtoState":
        """
        Returns self only if the state is FULL, otherwise raises an exception.
        """
        if self.get_type() == AssetDtoType.FULL:
            return self
        raise RuntimeError("AssetDtoState is not FULL; operation not allowed.")

    def get_is_favorite(self) -> bool:
        """
        Returns True if the asset is marked as favorite, False otherwise. Defensive: always returns a bool.
        """
        return self._dto.is_favorite

    def get_created_at(self) -> datetime:
        """
        Returns the created_at date of the asset, if available.
        """
        return self._dto.created_at

    def get_original_path(self) -> Path:
        """
        Returns the original file path of the asset.
        """
        return Path(self._dto.original_path)

    def get_duplicate_id_as_uuid(self) -> UUID:
        """
        Returns the duplicate id as UUID.
        """
        # Defensive: handle Unset/None/str for duplicate_id
        val = self._dto.duplicate_id
        if val is None or isinstance(val, Unset):
            raise NotImplementedError("Duplicate ID is not set or is unset")
        return UUID(val)
