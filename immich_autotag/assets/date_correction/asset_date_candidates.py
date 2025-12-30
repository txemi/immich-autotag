
import attrs
from typing import List, Iterator, Optional
from datetime import datetime
from typeguard import typechecked
from .asset_date_candidate import AssetDateCandidate

@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidates:

    candidates: List[AssetDateCandidate] = attrs.field(factory=list)
    @typechecked
    def add(self, candidate: AssetDateCandidate) -> None:
        self.candidates.append(candidate)
    @typechecked
    def extend(self, other: "AssetDateCandidates") -> None:
        self.candidates.extend(other.candidates)
    @typechecked
    def is_empty(self) -> bool:
        return not self.candidates
    @typechecked
    def oldest(self) -> Optional[datetime]:
        return min((c.date for c in self.candidates), default=None)
    @typechecked
    def all_dates(self) -> List[datetime]:
        return [c.date for c in self.candidates]
    @typechecked
    def __len__(self) -> int:
        return len(self.candidates)
    @typechecked
    def __iter__(self) -> Iterator["AssetDateCandidate"]:
        return iter(self.candidates)
    @typechecked
    def immich_date_is_oldest_or_equal(self, immich_date: datetime) -> bool:
        """
        Returns True if immich_date is less than or equal to all candidate dates.
        """
        return all(immich_date <= c.date for c in self.candidates)
    @typechecked
    def filename_candidates(self):
        """Return all candidates whose source_kind is FILENAME."""
        from .date_source_kind import DateSourceKind
        return [c for c in self.candidates if c.source_kind == DateSourceKind.FILENAME]
    @typechecked
    def all_candidates(self) -> List[AssetDateCandidate]:
        """Return all AssetDateCandidate objects (alias for list(self))."""
        return list(self.candidates)

    @typechecked
    def oldest_candidate(self) -> Optional[AssetDateCandidate]:
        """Return the AssetDateCandidate with the oldest date, or None if none found."""
        return min(self.candidates, key=lambda c: c.date) if self.candidates else None

    @typechecked
    def candidates_by_kind(self, kind) -> List[AssetDateCandidate]:
        """Return all candidates of a given DateSourceKind."""
        return [c for c in self.candidates if c.source_kind == kind]

    @typechecked
    def oldest_by_kind(self, kind) -> Optional[AssetDateCandidate]:
        """Return the oldest candidate of a given DateSourceKind, or None if none found."""
        filtered = self.candidates_by_kind(kind)
        return min(filtered, key=lambda c: c.date) if filtered else None

    @typechecked
    def has_kind(self, kind) -> bool:
        """Return True if there is at least one candidate of the given kind."""
        return any(c.source_kind == kind for c in self.candidates)