from typing import Iterator, List

import attrs

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class AssetResponseWrapperList:
    """
    Encapsula una lista de AssetResponseWrapper, proporcionando métodos utilitarios y deduplicación futura.
    """

    _assets: List[AssetResponseWrapper] = attrs.field(
        factory=list, repr=lambda assets: f"size={len(assets)}"
    )

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
