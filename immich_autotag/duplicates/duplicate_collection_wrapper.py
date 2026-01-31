from typing import TYPE_CHECKING, Dict, Optional
from urllib.parse import ParseResult
from uuid import UUID

import attrs
from immich_client.models.duplicate_response_dto import DuplicateResponseDto
from typeguard import typechecked

from immich_autotag.types.uuid_wrappers import AssetUUID, DuplicateUUID

if TYPE_CHECKING:
    from immich_autotag.assets.asset_manager import AssetManager
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAssetGroup:

    class DuplicateAssetGroupIterator:
        def __init__(self, assets: list[AssetUUID]):
            self._assets: list[AssetUUID] = assets
            self._index: int = 0

        def __next__(self) -> AssetUUID:
            if self._index < len(self._assets):
                result: AssetUUID = self._assets[self._index]
                self._index += 1
                return result
            raise StopIteration

        def __iter__(self) -> "DuplicateAssetGroup.DuplicateAssetGroupIterator":
            return self

    assets: list[AssetUUID]

    def as_str_list(self) -> list[str]:
        return [str(u) for u in self.assets]

    def __iter__(self) -> "DuplicateAssetGroup.DuplicateAssetGroupIterator":
        return DuplicateAssetGroup.DuplicateAssetGroupIterator(self.assets)

    def __len__(self) -> int:
        return len(self.assets)


@attrs.define(auto_attribs=True, slots=True)
class DuplicateCollectionWrapper:
    """
    Wrapper for the Immich duplicates database structure.
    Holds a mapping from duplicate_id (UUID) to DuplicateAssetGroup.
    """

    groups_by_duplicate_id: dict[DuplicateUUID, DuplicateAssetGroup]

    @classmethod
    @typechecked
    def from_api_response(
        cls: type["DuplicateCollectionWrapper"], data: list[DuplicateResponseDto]
    ) -> "DuplicateCollectionWrapper":
        """
        Builds the duplicate mapping from the API response, using duplicate_id as key and the asset list as DuplicateAssetGroup.
        """
        mapping: Dict[UUID, DuplicateAssetGroup] = {}
        for group in data:
            if not isinstance(group, DuplicateResponseDto):
                raise TypeError(f"Expected DuplicateResponseDto, got {type(group)}")
            duplicate_id = UUID(group.duplicate_id)
            asset_ids = [AssetUUID.from_uuid(UUID(asset.id)) for asset in group.assets]
            mapping[duplicate_id] = DuplicateAssetGroup(asset_ids)
        return cls(groups_by_duplicate_id=mapping)

    @typechecked
    def get_group(self, duplicate_id: DuplicateUUID) -> DuplicateAssetGroup:
        """Return the DuplicateAssetGroup for a given duplicate_id. Empty if not found."""
        return self.groups_by_duplicate_id.get(duplicate_id, DuplicateAssetGroup([]))

    @typechecked
    def get_duplicate_asset_links(
        self, duplicate_id: Optional[UUID]
    ) -> list[ParseResult]:
        """
        Returns a list of ParseResult (standard URL objects) for all assets in the duplicate group.
        duplicate_id: UUID
        """
        from immich_autotag.utils.url_helpers import get_immich_photo_url

        if duplicate_id is None:
            return []
        group: DuplicateAssetGroup = self.get_group(duplicate_id)
        # get_immich_photo_url already returns a ParseResult
        return [get_immich_photo_url(dup_id) for dup_id in group]

    @typechecked
    def get_duplicate_asset_wrappers(
        self,
        duplicate_id: UUID,
        asset_manager: "AssetManager",
        context: "ImmichContext",
    ) -> list["AssetResponseWrapper"]:
        """
        Returns a list of AssetResponseWrapper objects for all assets in the duplicate group.
        """
        group = self.get_group(duplicate_id)
        wrappers = []
        for asset_id in group:
            wrapper = asset_manager.get_asset(asset_id, context)
            if wrapper is not None:
                wrappers.append(wrapper)
        return wrappers
