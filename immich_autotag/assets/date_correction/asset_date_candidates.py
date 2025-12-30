
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

    def filename_candidates(self):
        """Return all candidates whose source_kind is FILENAME."""
        from .date_source_kind import DateSourceKind
        return [c for c in self.candidates if c.source_kind == DateSourceKind.FILENAME]
