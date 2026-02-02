from typing import TYPE_CHECKING, List

import attr
from typeguard import typechecked

from immich_autotag.classification.match_result import MatchResult

if TYPE_CHECKING:
    from immich_autotag.classification.classification_status import (
        ClassificationStatus,
    )


@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=True)
class MatchResultList:
    matches: List[MatchResult] = attr.ib(
        validator=attr.validators.deep_iterable(
            member_validator=attr.validators.instance_of(MatchResult),
            iterable_validator=attr.validators.instance_of(list),
        )
    )

    @typechecked
    def tags(self) -> list[str]:
        tags: list[str] = []
        for m in self.matches:
            tags.extend(m.tags_matched)
        return tags

    @typechecked
    def albums(self) -> list[str]:
        albums: list[str] = []
        for m in self.matches:
            albums.extend(m.albums_matched)
        return albums

    @typechecked
    def asset_links(self) -> list[str]:
        asset_links: list[str] = []
        for m in self.matches:
            asset_links.extend(m.asset_links_matched)
        return asset_links

    @typechecked
    def rules(self) -> list[MatchResult]:
        return list(self.matches)

    @typechecked
    def _count_total_destinations(self) -> int:
        """
        Count the total number of destinations (tags + albums + asset_links) across all match results.
        If a single rule produces multiple albums, tags, or asset_links, each counts as a destination.
        
        Returns:
            Total count of tags, albums, and asset_links matched.
        """
        total_tags = len(self.tags())
        total_albums = len(self.albums())
        total_asset_links = len(self.asset_links())
        return total_tags + total_albums + total_asset_links

    @typechecked
    def classification_status(self) -> "ClassificationStatus":
        """
        Determines the classification status based on number of matched rules.

        Returns the status as a ClassificationStatus enum, making it easy to
        pattern-match on the result for clear control flow.

        Returns:
            ClassificationStatus indicating if asset is CLASSIFIED, CONFLICT, or UNCLASSIFIED.

        Example:
            >>> status = match_results.classification_status()
            >>> match status:
            ...     case ClassificationStatus.CLASSIFIED:
            ...         # Handle classified asset
            ...     case ClassificationStatus.CONFLICT:
            ...         # Handle conflict
            ...     case ClassificationStatus.UNCLASSIFIED:
            ...         # Handle unclassified
        """
        from immich_autotag.classification.classification_status import (
            ClassificationStatus,
        )

        return ClassificationStatus.from_match_results(self)

    @typechecked
    def __getitem__(self, idx: int) -> MatchResult:
        return self.matches[idx]

    @typechecked
    def __len__(self) -> int:
        return len(self.matches)
