from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Mapping, NoReturn, cast

from immich_autotag.types.uuid_wrappers import AssetUUID, DuplicateUUID

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

import enum
from datetime import datetime

import attrs

from immich_autotag.api.logging_proxy.assets.get_asset_info import AssetResponseDto
from immich_autotag.api.logging_proxy.types import UNSET, Unset


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


# Exception for duplicate_id not loaded
class DuplicateIdNotLoadedError(Exception):
    pass


@attrs.define(auto_attribs=True, slots=True)
class AssetDtoState:
    """
    Encapsulates the current DTO, its type (partial/full), and the loaded_at timestamp.
    This class never performs API calls or business logic—just holds and exposes data.
    """

    _dto: AssetResponseDto | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(
            attrs.validators.instance_of(AssetResponseDto)
        ),
    )
    _api_endpoint_source: AssetDtoType | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(AssetDtoType)),
    )
    _loaded_at: datetime | None = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(datetime)),
    )

    def _require_dto(self) -> AssetResponseDto:
        """
        Returns the internal DTO if present, otherwise raises a RuntimeError.
        Centralizes the defensive check for DTO presence.
        """
        if self._dto is None:
            raise RuntimeError("DTO is None")
        return self._dto

    def _check_tag_type_integrity(self):
        """
        Validates that the tag type is consistent with the API endpoint source.
        This is a defensive check to ensure we understand the Immich API behavior correctly.

        Rules:
        - FULL mode: tags must be a list (loaded) or Unset (not yet loaded)
        - PARTIAL mode (SEARCH/ALBUM): tags must be a set or Unset
        """
        tags = self._dto.tags if self._dto is not None else None
        if self._api_endpoint_source == AssetDtoType.FULL:
            if tags is not None and not isinstance(tags, (list, Unset)):
                raise TypeError(
                    f"In FULL mode, tags must be a list or Unset, but it is {type(tags)}"
                )
        else:
            if tags is not None and not isinstance(tags, (set, Unset)):
                raise TypeError(
                    f"In PARTIAL mode (SEARCH/ALBUM), tags must be a set or Unset, but it is {type(tags)}"
                )

    def __attrs_post_init__(self):
        # Defensive check: only run if all required fields are set
        if self._dto is None or self._api_endpoint_source is None:
            return
        self._check_tag_type_integrity()
        # If more types are added, add more checks here

    def get_type(self) -> AssetDtoType:
        if self._api_endpoint_source is None:
            raise RuntimeError("AssetDtoState: _api_endpoint_source is None")
        return self._api_endpoint_source

    def get_loaded_at(self) -> datetime:
        if self._loaded_at is None:
            raise RuntimeError("AssetDtoState: _loaded_at is None")
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

        Uses the robust are_tags_loaded() validation to ensure:
        1. Tags are loaded (not Unset)
        2. We're in FULL mode
        3. Both validation methods agree

        Raises:
            TagsNotLoadedError: If tags are not loaded (Unset)
            RuntimeError: If validation methods disagree (inconsistent state)
        """
        # This will validate that tags are loaded using both methods
        full = self.require_tags_loaded()
        dto = full._require_dto()
        tags = dto.tags

        # Double-check: tags should NOT be Unset at this point
        if isinstance(tags, Unset):
            raise TagsNotLoadedError(
                "Tags are UNSET; tags have not been loaded for this asset. "
                "This should have been caught by require_tags_loaded()."
            )

        from immich_autotag.context.immich_context import ImmichContext

        tag_collection = ImmichContext.get_default_instance().get_tag_collection()
        wrappers: list["TagWrapper"] = []
        for tag in tags:
            wrapper = tag_collection.get_tag_from_dto(tag)
            if wrapper is not None:
                wrappers.append(wrapper)
        return wrappers

    def get_dates(self) -> list[datetime]:
        def _get_dates(asset__: AssetResponseDto) -> Iterator[datetime]:
            yield asset__.created_at
            yield asset__.file_created_at
            yield asset__.file_modified_at
            yield asset__.local_date_time

        dto = self._require_dto()
        date_candidates = list(_get_dates(dto))
        return date_candidates

    def has_tag(self, tag_name: str) -> bool:
        """
        Returns True if the asset has a tag with that name (case-insensitive), False otherwise.
        """
        tag_names = self.get_tag_names()
        return any(tn.lower() == tag_name.lower() for tn in tag_names)

    def get_uuid(self) -> AssetUUID:
        dto = self._require_dto()
        if not dto.id:
            raise RuntimeError("DTO is missing id")
        return AssetUUID(dto.id)

    def get_original_file_name(self) -> Path:
        dto = self._require_dto()
        if not dto.original_file_name:
            raise RuntimeError("DTO is missing original_file_name")
        return Path(dto.original_file_name)

    def to_cache_dict(self) -> dict[str, object]:
        """
        Serializes the state to a dictionary, including loaded_at in ISO format.
        """
        dto = self._require_dto()
        if self._api_endpoint_source is None or self._loaded_at is None:
            raise RuntimeError(
                "Cannot serialize AssetDtoState: missing required fields"
            )
        try:
            dto_data: dict[str, Any] = dto.to_dict()  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            dto_data = dto  # type: ignore[assignment]
        return {
            "dto": dto_data,
            "type": self._api_endpoint_source.value,
            "loaded_at": self._loaded_at.isoformat(),
        }

    @classmethod
    def from_dto(
        cls,
        dto: AssetResponseDto,
        api_endpoint_source: AssetDtoType,
        loaded_at: datetime | None = None,
    ) -> "AssetDtoState":
        # We use manual field assignment here to ensure validators and post-init logic are respected,
        # and to avoid issues with attrs' __init__ signature when using private fields.
        # See docs/dev/architecture.md#assetdtostate-constructor for rationale and details.
        self = cls()
        self._dto = dto
        self._api_endpoint_source = api_endpoint_source
        self._loaded_at = loaded_at if loaded_at is not None else datetime.now()
        self._check_tag_type_integrity()
        return self

    @classmethod
    def from_cache_dict(cls, data: dict[str, object]) -> "AssetDtoState":
        """
        Reconstructs the state from a serialized dictionary.
        """
        from immich_autotag.api.logging_proxy.types import AssetResponseDto

        dto = AssetResponseDto.from_dict(cast(Mapping[str, Any], data["dto"]))
        api_endpoint_source = AssetDtoType(str(data["type"]))
        loaded_at = datetime.fromisoformat(str(data["loaded_at"]))
        return cls.from_dto(dto, api_endpoint_source, loaded_at)

    def get_tag_names(self) -> list[str]:
        """
        Returns the names of the tags associated with this asset, or an empty list if there are no tags.
        """
        tag_wrappers = self.get_tags()
        return [tag_wrapper.get_name() for tag_wrapper in tag_wrappers]

    def are_tags_loaded(self) -> bool:
        """
        Returns True if tags are fully loaded (available for reading), False otherwise.

        This method performs DUAL validation to ensure consistency:
        1. Checks if we're in FULL mode (tags should be loaded in FULL mode)
        2. Checks if tags are NOT Unset (direct verification)

        Both checks should agree. If they don't, we raise an exception to catch API behavior mismatches early.

        Returns:
            True if tags are loaded and accessible
            False if tags are not loaded (Unset)

        Raises:
            RuntimeError: If the two validation methods disagree (inconsistent state)
        """
        dto = self._require_dto()
        tags = dto.tags

        # Direct check: are tags Unset?
        tags_are_unset = isinstance(tags, Unset)

        # Indirect check: are we in FULL mode?
        is_full_mode = self.get_type() == AssetDtoType.FULL

        # Defensive consistency check: both methods should agree
        if is_full_mode and tags_are_unset:
            raise RuntimeError(
                "Inconsistent state: AssetDtoType is FULL but tags are Unset. "
                "This suggests a mismatch between how we're tracking API endpoints and the actual data. "
                f"Asset ID: {dto.id}"
            )

        if not is_full_mode and not tags_are_unset and not isinstance(tags, set):
            raise RuntimeError(
                f"Inconsistent state: AssetDtoType is PARTIAL ({self.get_type().value}) but tags are neither Unset nor a set (type: {type(tags)}). "
                "This suggests unexpected API behavior. "
                f"Asset ID: {dto.id}"
            )

        # If we're here, both checks are consistent
        return not tags_are_unset

    def _raise_tags_not_loaded_error(self) -> NoReturn:
        """
        Raises an error indicating tags are not loaded. Separated for clarity.
        """
        raise RuntimeError(
            "Tags are not loaded (Unset). Cannot perform operation that requires full asset data. "
            f"Current state: {self.get_type().value}"
        )

    def require_tags_loaded(self) -> "AssetDtoState":
        """
        Ensures tags are fully loaded and returns self, otherwise raises an exception.

        This method uses the robust are_tags_loaded() validation which checks:
        1. That we're in FULL mode (old method)
        2. That tags are not Unset (new, more direct method)
        3. That both methods agree (defensive consistency check)

        Returns:
            self: Always returns self when tags are loaded

        Raises:
            RuntimeError: If tags are not loaded or if validation methods disagree
        """
        if self.are_tags_loaded():
            return self
        self._raise_tags_not_loaded_error()

    def get_is_favorite(self) -> bool:
        """
        Returns True if the asset is marked as favorite, False otherwise. Defensive: always returns a bool.
        """
        dto = self._require_dto()
        return bool(dto.is_favorite)

    def get_created_at(self) -> datetime:
        """
        Returns the created_at date of the asset, if available.
        """
        dto = self._require_dto()
        if not dto.created_at:
            raise RuntimeError("DTO is missing created_at")
        return dto.created_at

    def get_original_path(self) -> Path:
        """
        Returns the original file path of the asset.
        """
        dto = self._require_dto()
        if not dto.original_path:
            raise RuntimeError("DTO is missing original_path")
        return Path(dto.original_path)

    def is_duplicate_id_loaded(self) -> bool:
        """
        Returns True if duplicate_id is loaded (not Unset), False otherwise.

        Similar to are_tags_loaded(), this checks if the duplicate_id field has been loaded.
        The duplicate_id may be Unset depending on which API endpoint was used.

        Note: This returns True even if duplicate_id is None/empty (meaning the asset
        is not part of any duplicate group). It only returns False if the field is Unset
        (meaning we haven't loaded it yet).

        Returns:
            True if duplicate_id is loaded (accessible, even if None/empty)
            False if duplicate_id is Unset (not yet loaded)
        """
        dto = self._require_dto()
        val = dto.duplicate_id

        # Check if the field is Unset (not loaded)
        if val is UNSET or isinstance(val, Unset):
            return False

        # Field is loaded (even if it's None or empty string)
        return True

    def _raise_duplicate_id_not_loaded_error(self) -> NoReturn:
        """
        Raises an error indicating duplicate_id is not loaded. Separated for clarity.
        """
        raise DuplicateIdNotLoadedError(
            f"duplicate_id is not loaded (Unset). Cannot access duplicate_id that requires full asset data. "
            f"Current API source: {self.get_type().value}. "
            f"The upper layer should call ensure_full_asset_loaded() before accessing duplicate_id."
        )

    def require_duplicate_id_loaded(self) -> "AssetDtoState":
        """
        Ensures duplicate_id is loaded and returns self, otherwise raises an exception.

        This forces the caller (upper layer) to handle the case where duplicate_id
        is not loaded, typically by calling ensure_full_asset_loaded() first.

        Returns:
            self: Always returns self when duplicate_id is loaded

        Raises:
            DuplicateIdNotLoadedError: If duplicate_id is not loaded (Unset)
        """
        if self.is_duplicate_id_loaded():
            return self
        self._raise_duplicate_id_not_loaded_error()

    def get_duplicate_id_as_uuid(self) -> DuplicateUUID | None:
        """
        Returns the duplicate_id as a DuplicateUUID, or None if the asset has no duplicate group.

        This method requires duplicate_id to be loaded. If not loaded (Unset), it raises
        DuplicateIdNotLoadedError, forcing the upper layer to call ensure_full_asset_loaded().

        Returns:
            DuplicateUUID if the asset is part of a duplicate group
            None if the asset is NOT part of any duplicate group (field is loaded but empty)

        Raises:
            DuplicateIdNotLoadedError: If duplicate_id is Unset (not yet loaded from API)
        """
        # Ensure duplicate_id is loaded (will raise if Unset)
        full = self.require_duplicate_id_loaded()
        dto = full._require_dto()
        val = dto.duplicate_id

        # At this point, val is NOT Unset (validated by require_duplicate_id_loaded)
        # But it might be None or empty string, meaning no duplicate group
        if not val:
            return None

        return DuplicateUUID(val)
