
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from datetime import datetime
from typing import Optional

import attrs
from typeguard import typechecked

from .asset_date_candidates import AssetDateCandidate, AssetDateCandidates


@attrs.define(auto_attribs=True, slots=True)
class AssetDateSourcesList:

    """
    Holds a list of AssetDateCandidates sets, one for each duplicate asset (AssetResponseWrapper).
    Each entry in candidates_list is an AssetDateCandidates object for a specific asset/duplicate.
    The asset_wrapper field indicates the asset that triggered this investigation.

    Example usage:
        sources_list = AssetDateSourcesList.from_wrappers(main_asset_wrapper, [wrapper1, wrapper2, ...])
        print(sources_list.asset_wrapper)  # asset that triggered
        for candidate_set in sources_list.candidates_list:
            ...

    TODO: Consider renaming to AssetDateCandidatesList for clarity.
    """

    asset_wrapper: "AssetResponseWrapper" = attrs.field()
    candidates_list: list[AssetDateCandidates] = attrs.field(factory=list)

    @typechecked
    def add(self, candidate_set: AssetDateCandidates) -> None:
        self.candidates_list.append(candidate_set)

    @typechecked
    def extend(self, candidate_sets: list[AssetDateCandidates]) -> None:
        self.candidates_list.extend(candidate_sets)

    @typechecked
    def __len__(self) -> int:
        return len(self.candidates_list)

    @typechecked
    def __iter__(self):
        return iter(self.candidates_list)

    @staticmethod
    @typechecked
    def from_wrappers(
        asset_wrapper: "AssetResponseWrapper", wrappers: list["AssetResponseWrapper"]
    ) -> "AssetDateSourcesList":
        """
        Build an AssetDateSourcesList from a main AssetResponseWrapper and a list of AssetResponseWrapper objects (duplicates).
        Each wrapper gets its own AssetDateCandidates set.
        """
        from .get_asset_date_sources import get_asset_date_candidates

        if not wrappers:
            raise ValueError("wrappers list must not be empty")
        candidate_sets = [get_asset_date_candidates(w) for w in wrappers]
        return AssetDateSourcesList(asset_wrapper, candidate_sets)

    @typechecked
    def get_whatsapp_filename_date(self) -> Optional[datetime]:
        """
        Return the minimum (oldest) non-None whatsapp_filename_date among all candidates in all sets, or None if none present.
        """
        from .date_source_kind import DateSourceKind

        dates = [
            c.get_aware_date()
            for candidate_set in self.candidates_list
            for c in candidate_set.candidates
            if c.source_kind == DateSourceKind.WHATSAPP_FILENAME
        ]
        return min(dates) if dates else None

    @typechecked
    def to_flat_candidates(self) -> list[AssetDateCandidate]:
        """
        Return a flat list of all AssetDateCandidate objects from all sets.
        """
        return [
            c
            for candidate_set in self.candidates_list
            for c in candidate_set.candidates
        ]

    @typechecked
    def filename_candidates(self) -> list[AssetDateCandidate]:
        """
        Devuelve todos los candidatos de tipo FILENAME de todos los sets de candidatos.
        """
        result = []
        for candidate_set in self.candidates_list:
            result.extend(candidate_set.filename_candidates())
        return result
    @typechecked
    def oldest_candidate(self) -> Optional["AssetDateCandidate"]:
        """
        Devuelve el AssetDateCandidate más antiguo entre todos los duplicados.
        """
        all_candidates = [cset.oldest_candidate() for cset in self.candidates_list if cset.oldest_candidate() is not None]
        if not all_candidates:
            return None
        return min(all_candidates)