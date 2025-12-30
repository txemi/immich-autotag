from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from typeguard import typechecked
import attrs
from typing import List
from .asset_date_sources import AssetDateSources
from .asset_date_candidates import AssetDateCandidates


from typing import Optional
from datetime import datetime
from typeguard import typechecked


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

    @typechecked
    def get_whatsapp_filename_date(self) -> Optional[datetime]:
        """
        Return the minimum (oldest) non-None whatsapp_filename_date among all sources, or None if none present.
        """
        dates = [
            src.whatsapp_filename_date
            for src in self.sources
            if src.whatsapp_filename_date is not None
        ]
        return min(dates) if dates else None

    @typechecked
    def to_candidates(self) -> AssetDateCandidates:
        """
        Return an AssetDateCandidates object with all AssetDateCandidate objects from all sources.
        """
        candidates = AssetDateCandidates()
        for src in self.sources:
            candidates.candidates.extend(src.all_candidates())
        return candidates
