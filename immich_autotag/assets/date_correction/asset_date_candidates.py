
from typing import List
from datetime import datetime
from typeguard import typechecked
from .asset_date_candidate import AssetDateCandidate

@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidates:
    candidates: List[AssetDateCandidate] = attrs.field(factory=list)

    def add(self, candidate: AssetDateCandidate) -> None:
        self.candidates.append(candidate)

    def extend(self, other: "AssetDateCandidates") -> None:
        self.candidates.extend(other.candidates)

    def is_empty(self) -> bool:
        return not self.candidates

    def oldest(self) -> datetime:
        return min((c.date for c in self.candidates), default=None)

    def all_dates(self) -> List[datetime]:
        return [c.date for c in self.candidates]

    def __len__(self):
        return len(self.candidates)

    def __iter__(self):
        return iter(self.candidates)

    def immich_date_is_oldest_or_equal(self, immich_date) -> bool:
        """
        Returns True if immich_date is less than or equal to all candidate dates.
        """
        return all(immich_date <= c.date for c in self.candidates)
