from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, List

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
# Removed top-level import to avoid circular import


@attrs.define(auto_attribs=True, slots=True)
class AssetResponseWrapperList:
    """
    Encapsulates a collection of AssetResponseWrapper, providing utility methods and future deduplication.
    """

    _assets: List[AssetResponseWrapper] = attrs.field(
        factory=list, repr=lambda assets: f"size={len(assets)}"
    )

    @typechecked
    def append(self, asset: AssetResponseWrapper) -> None:
        self._assets.append(asset)

    def to_list(self) -> List[AssetResponseWrapper]:
        return list(self._assets)

    def __getitem__(self, idx: int) -> AssetResponseWrapper:
        return self._assets[idx]

    def __iter__(self) -> Iterator[AssetResponseWrapper]:
        return iter(self._assets)

    def __len__(self) -> int:
        return len(self._assets)
