
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
    def from_api_response(cls, data: Any) -> "DuplicateCollectionWrapper":
        # data is a list of DuplicateResponseDto
        mapping = {entry.asset_id: entry.duplicates for entry in data}
        return cls(duplicates_by_asset=mapping)

    @typechecked
    def get_duplicates(self, asset_id: str) -> List[str]:
        """Return the list of duplicate asset IDs for a given asset_id."""
        return self.duplicates_by_asset.get(asset_id, [])
