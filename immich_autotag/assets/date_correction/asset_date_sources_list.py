from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from typeguard import typechecked
import attrs
from typing import List
from .asset_date_sources import AssetDateSources

@attrs.define(auto_attribs=True, slots=True)
class AssetDateSourcesList:


    sources: List[AssetDateSources] = attrs.field(factory=list)

    @typechecked
    def add(self, source: AssetDateSources) -> None:
        self.sources.append(source)

    @typechecked
    def extend(self, sources: List[AssetDateSources]) -> None:
        self.sources.extend(sources)

    @typechecked
    def add_all_candidates_to(self, candidates: list) -> None:
        for src in self.sources:
            src.add_candidates_to(candidates)

    @typechecked
    def __len__(self) -> int:
        return len(self.sources)

    @typechecked
    def __iter__(self):
        return iter(self.sources)
    @staticmethod
    @typechecked
    def from_wrappers(wrappers: list["AssetResponseWrapper"]) -> "AssetDateSourcesList":
        """
        Build an AssetDateSourcesList from a list of AssetResponseWrapper objects.
        """
        from .get_asset_date_sources import get_asset_date_sources
        sources = [get_asset_date_sources(w) for w in wrappers]
        return AssetDateSourcesList(sources)