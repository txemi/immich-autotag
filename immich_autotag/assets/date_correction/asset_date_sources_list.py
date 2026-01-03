from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from datetime import datetime
from typing import Optional

import attrs
from typeguard import typechecked

from .asset_date_candidates import AssetDateCandidate, AssetDateCandidates
from .date_source_kind import DateSourceKind


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
    # Each element represents the date candidates of a duplicate asset
    date_candidates_per_duplicate: list[AssetDateCandidates] = attrs.field(factory=list)

    @typechecked
    def add(self, candidate_set: AssetDateCandidates) -> None:
        self.date_candidates_per_duplicate.append(candidate_set)

    @typechecked
    def extend(self, candidate_sets: list[AssetDateCandidates]) -> None:
        self.date_candidates_per_duplicate.extend(candidate_sets)

    @typechecked
    def __len__(self) -> int:
        return len(self.date_candidates_per_duplicate)

    @typechecked
    def __iter__(self):
        return iter(self.date_candidates_per_duplicate)

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
            for candidate_set in self.date_candidates_per_duplicate
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
            for candidate_set in self.date_candidates_per_duplicate
            for c in candidate_set.candidates
        ]

    @typechecked
    def filename_candidates(self) -> list[AssetDateCandidate]:
        """
        Returns all FILENAME type candidates from all candidate sets.
        """
        result = []
        for candidate_set in self.date_candidates_per_duplicate:
            result.extend(candidate_set.filename_candidates())
        return result

    @typechecked
    def oldest_candidate(self) -> Optional["AssetDateCandidate"]:
        """
        Returns the oldest AssetDateCandidate among all duplicates.
        """
        all_candidates = [
            cset.oldest_candidate()
            for cset in self.date_candidates_per_duplicate
            if cset.oldest_candidate() is not None
        ]
        if not all_candidates:
            return None
        return min(all_candidates)

    @typechecked
    def format_full_info(self) -> str:
        lines = []
        lines.append("==== [AssetDateSourcesList] Complete diagnosis ====")
        lines.append(f"Main asset: {self.asset_wrapper.format_info()}")
        lines.append("")
        for i, candidate_set in enumerate(self.date_candidates_per_duplicate):
            lines.append(f"--- Duplicate #{i+1} ---")
            lines.append(candidate_set.format_info())
            lines.append("")
        return "\n".join(lines)

    @typechecked
    def candidates_by_kinds(
        self, kinds: list[DateSourceKind]
    ) -> list[AssetDateCandidate]:
        """Returns all candidates from all duplicates whose source_kind is in the kinds list."""
        result = []
        for candidate_set in self.date_candidates_per_duplicate:
            result.extend(candidate_set.candidates_by_kinds(kinds))
        return result
