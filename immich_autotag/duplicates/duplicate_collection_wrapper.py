
import attrs
from typeguard import typechecked
from typing import Any, Dict, List
from immich_client.models.duplicate_response_dto import DuplicateResponseDto

@attrs.define(auto_attribs=True, slots=True)
class DuplicateCollectionWrapper:
    """
    Wrapper for the Immich duplicates database structure.
    Holds a mapping from asset_id to list of duplicate asset_ids.
    """
    duplicates_by_asset: Dict[str, List[str]]

    @classmethod
    @typechecked
    def from_api_response(
        cls, data: List[DuplicateResponseDto]
    ) -> "DuplicateCollectionWrapper":
        """
        Construye el mapping de duplicados a partir de la respuesta de la API.
        """
        mapping: Dict[str, List[str]] = {}
        for group in data:
            if not isinstance(group, DuplicateResponseDto):
                raise TypeError(f"Expected DuplicateResponseDto, got {type(group)}")
            asset_ids = [asset.id for asset in group.assets]
            for asset_id in asset_ids:
                mapping[asset_id] = [other_id for other_id in asset_ids if other_id != asset_id]
        return cls(duplicates_by_asset=mapping)

    @typechecked
    def get_duplicates(self, asset_id: str) -> List[str]:
        """Return the list of duplicate asset IDs for a given asset_id."""
        return self.duplicates_by_asset.get(asset_id, [])
