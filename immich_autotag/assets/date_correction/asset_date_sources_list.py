from datetime import datetime
from typing import TYPE_CHECKING, Optional

import attrs
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper_list import AssetResponseWrapperList
from immich_autotag.assets.validators import validate_asset_response_wrapper_not_none

from .asset_date_candidate import AssetDateCandidate
from .asset_date_candidates import AssetDateCandidates
from .date_source_kind import DateSourceKind

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


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

    _asset_wrapper: "AssetResponseWrapper" = attrs.field(
        validator=validate_asset_response_wrapper_not_none
    )
    # Each element represents the date candidates of a duplicate asset
    _date_candidates_per_duplicate: list[AssetDateCandidates] = attrs.field(
        factory=list
    )

    @typechecked
    def get_asset_wrapper(self) -> "AssetResponseWrapper":
        return self._asset_wrapper

    @typechecked
    def get_date_candidates_per_duplicate(self) -> list[AssetDateCandidates]:
        return self._date_candidates_per_duplicate

    # Holds a list of AssetDateCandidates sets, one for each duplicate asset (AssetResponseWrapper).
    # Each entry in candidates_list is an AssetDateCandidates object for a specific asset/duplicate.
    # The asset_wrapper field indicates the asset that triggered this investigation.
    # TODO: Consider renaming to AssetDateCandidatesList for clarity.

    @typechecked
    def add(self, candidate_set: AssetDateCandidates) -> None:
        self._date_candidates_per_duplicate.append(candidate_set)

    @typechecked
    def extend(self, candidate_sets: list[AssetDateCandidates]) -> None:
        self._date_candidates_per_duplicate.extend(candidate_sets)

    @staticmethod
    @typechecked
    def from_wrappers(
        asset_wrapper: "AssetResponseWrapper", wrappers: "AssetResponseWrapperList"
    ) -> "AssetDateSourcesList":
        """
        Build an AssetDateSourcesList from a main AssetResponseWrapper and an AssetResponseWrapperList (duplicates).
        Each wrapper gets its own AssetDateCandidates set.
        """
        from .get_asset_date_sources import get_asset_date_candidates

        if not wrappers or len(wrappers) == 0:
            raise ValueError("wrappers list must not be empty")
        sources_list = AssetDateSourcesList(asset_wrapper)
        for w in wrappers:
            candidate_set = get_asset_date_candidates(w)
            sources_list.add(candidate_set)
        return sources_list

    @typechecked
    def get_whatsapp_filename_date(self) -> Optional[datetime]:
        """
        Return the minimum (oldest) non-None whatsapp_filename_date among all candidates in all sets, or None if none present.
        """
        from .date_source_kind import DateSourceKind

        dates = [
            c.get_aware_date()
            for candidate_set in self.get_date_candidates_per_duplicate()
            for c in candidate_set.all_candidates()
            if c.get_source_kind() == DateSourceKind.WHATSAPP_FILENAME
        ]
        return min(dates) if dates else None

    @typechecked
    def to_flat_candidates(self) -> list[AssetDateCandidate]:
        """
        Return a flat list of all AssetDateCandidate objects from all sets.
        """
        return [
            c
            for candidate_set in self.get_date_candidates_per_duplicate()
            for c in candidate_set.all_candidates()
        ]

    @typechecked
    def filename_candidates(self) -> list[AssetDateCandidate]:
        """
        Returns all FILENAME type candidates from all candidate sets.
        """
        result: list[AssetDateCandidate] = []
        for candidate_set in self.get_date_candidates_per_duplicate():
            result.extend(candidate_set.filename_candidates())
        return result

    @typechecked
    def oldest_candidate(self) -> Optional["AssetDateCandidate"]:
        """
        Returns the oldest AssetDateCandidate among all duplicates.
        """
        all_candidates: list[AssetDateCandidate] = []
        for cset in self.get_date_candidates_per_duplicate():
            candidate = cset.oldest_candidate()
            if candidate is not None:
                all_candidates.append(candidate)
        if not all_candidates:
            return None
        return min(all_candidates, key=lambda c: c.get_aware_date())

    @typechecked
    def format_full_info(self) -> str:
        lines: list[str] = []
        lines.append("==== [AssetDateSourcesList] Complete diagnosis ====")
        lines.append(f"Main asset: {self.get_asset_wrapper().format_info()}")
        lines.append("")
        for i, candidate_set in enumerate(self.get_date_candidates_per_duplicate()):
            lines.append(f"--- Duplicate #{i+1} ---")
            lines.append(candidate_set.format_info())
            lines.append("")
        return "\n".join(lines)

    @typechecked
    def candidates_by_kinds(
        self, kinds: list[DateSourceKind]
    ) -> list[AssetDateCandidate]:
        """Returns all candidates from all duplicates whose source_kind is in the kinds list."""
        result: list[AssetDateCandidate] = []
        for candidate_set in self.get_date_candidates_per_duplicate():
            result.extend(candidate_set.candidates_by_kinds(kinds))
        return result

    @typechecked
    def own_candidates_by_kinds(
        self, kinds: list[DateSourceKind]
    ) -> list[AssetDateCandidate]:
        """Returns the candidates of the main asset only (not of its duplicates) whose source_kind is in kinds."""
        main_id = self.get_asset_wrapper().get_id()
        result: list[AssetDateCandidate] = []
        for candidate_set in self.get_date_candidates_per_duplicate():
            if candidate_set.get_asset_wrapper().get_id() == main_id:
                result.extend(candidate_set.candidates_by_kinds(kinds))
        return result

    @staticmethod
    @typechecked
    def from_main_asset_wrapper(
        asset_wrapper: "AssetResponseWrapper",
    ) -> "AssetDateSourcesList":
        """
        Create an AssetDateSourcesList with only the main asset wrapper and no candidates.
        """
        return AssetDateSourcesList(asset_wrapper)

    @typechecked
    def __iter__(self):
        return iter(self.get_date_candidates_per_duplicate())

    @typechecked
    def __len__(self) -> int:
        return len(self.get_date_candidates_per_duplicate())
