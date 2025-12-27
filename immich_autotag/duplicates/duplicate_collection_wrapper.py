
import attrs
from typeguard import typechecked
from typing import Any, Dict, List
from uuid import UUID
from immich_client.models.duplicate_response_dto import DuplicateResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAssetGroup:
    assets: list[UUID]

    def __iter__(self) -> 'DuplicateAssetGroupIterator':
        return iter(self.assets)

    def __len__(self) -> int:
        return len(self.assets)

    def as_str_list(self) -> list[str]:
        return [str(u) for u in self.assets]


@attrs.define(auto_attribs=True, slots=True)

class DuplicateCollectionWrapper:


    """
    Wrapper for the Immich duplicates database structure.
    Holds a mapping from duplicate_id (UUID) to DuplicateAssetGroup.
    """
    groups_by_duplicate_id: dict[UUID, DuplicateAssetGroup]

    @classmethod
    @typechecked
    def from_api_response(
        cls: type['DuplicateCollectionWrapper'], data: list[DuplicateResponseDto]
    ) -> 'DuplicateCollectionWrapper':
        """
        Construye el mapping de duplicados a partir de la respuesta de la API, usando duplicate_id como clave y la lista de assets como DuplicateAssetGroup.
        """
        mapping: Dict[UUID, DuplicateAssetGroup] = {}
        for group in data:
            if not isinstance(group, DuplicateResponseDto):
                raise TypeError(f"Expected DuplicateResponseDto, got {type(group)}")
            duplicate_id = UUID(group.duplicate_id)
            asset_ids = [UUID(asset.id) for asset in group.assets]
            mapping[duplicate_id] = DuplicateAssetGroup(asset_ids)
        return cls(groups_by_duplicate_id=mapping)

    @typechecked
    def get_group(self, duplicate_id: UUID) -> DuplicateAssetGroup:
        """Return the DuplicateAssetGroup for a given duplicate_id. Empty if not found."""
        return self.groups_by_duplicate_id.get(duplicate_id, DuplicateAssetGroup([]))
    @typechecked
    def get_duplicate_asset_links(self, duplicate_id: UUID) -> list[str]:
        """
        Returns a list of asset links for all assets in the duplicate group.
        duplicate_id: UUID
        """
        from immich_autotag.utils.helpers import get_immich_photo_url
        if duplicate_id is None:
            return []
        group = self.get_group(duplicate_id)
        return [get_immich_photo_url(str(dup_id)) for dup_id in group]