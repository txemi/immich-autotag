import attrs
from typing import List, Tuple
from datetime import datetime
from datetime import datetime
from typing import Optional
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidates:

    candidates: List[Tuple[str, datetime]] = attrs.field(factory=list)

    def add(self, label: str, dt: datetime) -> None:
        self.candidates.append((label, dt))

    def extend(self, other: "AssetDateCandidates") -> None:
        self.candidates.extend(other.candidates)

    def is_empty(self) -> bool:
        return not self.candidates

    def oldest(self) -> datetime:
        return min((dt for _, dt in self.candidates), default=None)

    def all_dates(self) -> List[datetime]:
        return [dt for _, dt in self.candidates]

    def __len__(self):
        return len(self.candidates)

    def __iter__(self):
        return iter(self.candidates)

    def immich_date_is_oldest_or_equal(self, immich_date) -> bool:
        """
        Returns True if immich_date is less than or equal to all candidate dates.
        """
        return all(immich_date <= d for d in self.all_dates())
