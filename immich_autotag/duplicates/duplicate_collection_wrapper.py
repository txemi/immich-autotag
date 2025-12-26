
import attrs
from typeguard import typechecked
from typing import Any, Dict, List, Union
from uuid import UUID
from immich_client.models.duplicate_response_dto import DuplicateResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAssetList:
    uuids: List[UUID]

    def __contains__(self, item: Union[str, UUID]) -> bool:
        if isinstance(item, str):
            try:
                item = UUID(item)
            except Exception:
                return False
        return item in self.uuids

    def as_str_list(self) -> List[str]:
        return [str(u) for u in self.uuids]

    def __iter__(self):
        return iter(self.uuids)

    def __len__(self):
        return len(self.uuids)


@attrs.define(auto_attribs=True, slots=True)
class DuplicateCollectionWrapper:
    """
    Wrapper for the Immich duplicates database structure.
    Holds a mapping from asset UUID to DuplicateAssetList.
    """
    duplicates_by_asset: Dict[UUID, DuplicateAssetList]

    @classmethod
    @typechecked
    def from_api_response(
        cls, data: List[DuplicateResponseDto]
    ) -> "DuplicateCollectionWrapper":
        """
        Construye el mapping de duplicados a partir de la respuesta de la API, usando UUID y DuplicateAssetList.
        """
        mapping: Dict[UUID, DuplicateAssetList] = {}
        for group in data:
            if not isinstance(group, DuplicateResponseDto):
                raise TypeError(f"Expected DuplicateResponseDto, got {type(group)}")
            asset_ids = [UUID(asset.id) for asset in group.assets]
            for asset_id in asset_ids:
                others = [other_id for other_id in asset_ids if other_id != asset_id]
                mapping[asset_id] = DuplicateAssetList(others)
        return cls(duplicates_by_asset=mapping)

    @typechecked
    def get_duplicates(self, asset_id: Union[str, UUID]) -> DuplicateAssetList:
        """Return the DuplicateAssetList for a given asset_id (str or UUID). Empty if not found."""
        if isinstance(asset_id, str):
            try:
                asset_id = UUID(asset_id)
            except Exception:
                return DuplicateAssetList([])
        return self.duplicates_by_asset.get(asset_id, DuplicateAssetList([]))
