from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from typeguard import typechecked
import attrs
from .asset_date_candidates import AssetDateCandidates, AssetDateCandidate


from typing import Optional
from datetime import datetime
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AssetDateSourcesList:
    candidates: AssetDateCandidates = attrs.field(factory=AssetDateCandidates)

    @typechecked
    def add(self, candidate: AssetDateCandidate) -> None:
        self.candidates.add(candidate)

    @typechecked
    def extend(self, candidates: list[AssetDateCandidate]) -> None:
        for candidate in candidates:
            self.candidates.add(candidate)

    @typechecked
    def __len__(self) -> int:
        return len(self.candidates)

    @typechecked
    def __iter__(self):
        return iter(self.candidates)

    @staticmethod
    @typechecked
    def from_wrappers(wrappers: list["AssetResponseWrapper"]) -> "AssetDateSourcesList":
        """
        Build an AssetDateSourcesList from a list of AssetResponseWrapper objects.
        """
        from .get_asset_date_sources import get_asset_date_candidates
        all_candidates = AssetDateCandidates()
        for w in wrappers:
            candidates = get_asset_date_candidates(w)
            all_candidates.extend(candidates)
        return AssetDateSourcesList(all_candidates)

    @typechecked
    def get_whatsapp_filename_date(self) -> Optional[datetime]:
        """
        Return the minimum (oldest) non-None whatsapp_filename_date among all candidates, or None if none present.
        """
        from .date_source_kind import DateSourceKind
        dates = [
            c.date
            for c in self.candidates
            if c.source_kind == DateSourceKind.WHATSAPP_FILENAME
        ]
        return min(dates) if dates else None

    @typechecked
    def to_candidates(self) -> AssetDateCandidates:
        """
        Return the AssetDateCandidates object (all candidates).
        """
        return self.candidates
