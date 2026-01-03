from datetime import datetime
from typing import Iterator, List, Optional

import attrs
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from .asset_date_candidate import AssetDateCandidate
from .date_source_kind import DateSourceKind


@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidates:
    """
    Represents the collection of candidate dates provided by a single asset (active).
    Each instance of this class groups all possible dates extracted from different sources (Immich, filename, EXIF, etc.) for that specific asset.

    - asset_wrapper: Reference to the asset from which candidate dates were extracted.
    - candidates: List of AssetDateCandidate, each representing a date source for this asset.

    Example: An asset can have dates from Immich, filename, path, EXIF, etc. All those dates are grouped here.
    """

    asset_wrapper: AssetResponseWrapper = attrs.field()
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
        return min((c.get_aware_date() for c in self.candidates), default=None)

    @typechecked
    def all_dates(self) -> List[datetime]:
        return [c.get_aware_date() for c in self.candidates]

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
        return all(immich_date <= c.get_aware_date() for c in self.candidates)

    @typechecked
    def filename_candidates(self):
        """Return all candidates whose source_kind is FILENAME."""
        from .date_source_kind import DateSourceKind

        return [c for c in self.candidates if c.source_kind == DateSourceKind.FILENAME]

    @typechecked
    def all_candidates(self) -> List[AssetDateCandidate]:
        """Return all AssetDateCandidate objects (alias for list(self))."""
        return list(self.candidates)

    # Simplified and robust version, using AssetDateCandidate comparison
    @typechecked
    def oldest_candidate(self) -> Optional[AssetDateCandidate]:
        """
        Returns the AssetDateCandidate with the oldest date for this asset.
        """
        if not self.candidates:
            return None
        return min(self.candidates)

    @typechecked
    def candidates_by_kind(self, kind: DateSourceKind) -> List[AssetDateCandidate]:
        """Return all candidates of a given DateSourceKind."""
        return [c for c in self.candidates if c.source_kind == kind]

    @typechecked
    def oldest_by_kind(self, kind: DateSourceKind) -> Optional[AssetDateCandidate]:
        """Return the oldest candidate of a given DateSourceKind, or None if none found."""
        filtered = self.candidates_by_kind(kind)
        return min(filtered, key=lambda c: c.get_aware_date()) if filtered else None

    @typechecked
    def has_kind(self, kind: DateSourceKind) -> bool:
        """Return True if there is at least one candidate of the given kind."""
        return any(c.source_kind == kind for c in self.candidates)

    @typechecked
    def format_info(self) -> str:
        aw = self.asset_wrapper
        lines = [f"[AssetDateCandidates] Asset: {aw.id} | {aw.original_file_name}"]
        lines.append(f"  Link: {aw.get_immich_photo_url().geturl()}")
        lines.append(
            f"  Main dates: created_at={aw.asset.created_at}, file_created_at={getattr(aw.asset, 'file_created_at', None)}, exif_created_at={getattr(aw.asset, 'exif_created_at', None)}"
        )
        lines.append(f"  Tags: {aw.get_tag_names()}")
        lines.append(f"  Albums: {aw.get_album_names()}")
        lines.append("  Date candidates:")
        for c in self.candidates:
            lines.append("    " + c.format_info())
        return "\n".join(lines)

    @typechecked
    def candidates_by_kinds(
        self, kinds: list[DateSourceKind]
    ) -> List[AssetDateCandidate]:
        """Returns all candidates whose source_kind is in the kinds list."""
        return [c for c in self.candidates if c.source_kind in kinds]
