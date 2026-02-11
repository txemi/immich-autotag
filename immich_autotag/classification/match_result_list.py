from typing import TYPE_CHECKING, List

import attr
from typeguard import typechecked

from immich_autotag.classification.match_result import MatchResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )
    from immich_autotag.classification.classification_status import (
        ClassificationStatus,
    )


@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=False)
class MatchResultList:
    _rules: "ClassificationRuleSet" = attr.ib(init=True, repr=False)
    _asset: "AssetResponseWrapper" = attr.ib(
        init=True,
        repr=lambda asset: f"AssetResponseWrapper(url={asset.get_immich_photo_url().geturl()})",
    )
    _matches: List[MatchResult] = attr.ib(init=False, default=None, repr=False)

    @classmethod
    @typechecked
    def from_rules_and_asset(
        cls,
        rules: "ClassificationRuleSet",
        asset: "AssetResponseWrapper",
    ) -> "MatchResultList":
        """
        Factory method to create a MatchResultList with lazy loading of matches.

        The matches are NOT computed during construction. They are computed on demand
        when first accessed through a public method. This allows efficient lazy loading.

        Args:
            rules: The ClassificationRuleSet to match against the asset.
            asset: The AssetResponseWrapper to match with the rules.

        Returns:
            A new MatchResultList instance (matches will be computed on first access).
        """
        return cls(rules=rules, asset=asset)

    @typechecked
    def _get_matches(self) -> List[MatchResult]:
        """
        Private method to get matches with lazy loading.
        Computes matches on first call, subsequent calls return cached result.
        Delegates matching logic to ClassificationRuleSet for better separation.
        """
        if self._matches is None:
            self._matches = self._rules.match_asset(self._asset)
        return self._matches

    @typechecked
    def tags(self) -> list[str]:
        """Returns the list of all tags matched by classification rules (lazy loaded)."""
        tags: list[str] = []
        for m in self._get_matches():
            tags.extend(m.tags_matched())
        return tags

    @typechecked
    def albums(self) -> list[str]:
        """Returns the list of all albums matched by classification rules (lazy loaded)."""
        albums: list[str] = []
        for m in self._get_matches():
            albums.extend(m.albums_matched())
        return albums

    @typechecked
    def asset_links(self) -> list[str]:
        """Returns the list of all asset_links matched by classification rules (lazy loaded)."""
        asset_links: list[str] = []
        for m in self._get_matches():
            asset_links.extend(m.asset_links_matched())
        return asset_links

    @typechecked
    def rules(self) -> list[MatchResult]:
        """Returns the list of matched rules (lazy loaded)."""
        return list(self._get_matches())

    @typechecked
    def _count_total_destinations(self) -> int:
        """
        Count the total number of destinations (tags + albums + asset_links) across all match results.
        If a single rule produces multiple albums, tags, or asset_links, each counts as a destination.

        Returns:
            Total count of tags, albums, and asset_links matched (lazy loaded).
        """
        total_tags = len(self.tags())
        total_albums = len(self.albums())
        total_asset_links = len(self.asset_links())
        return total_tags + total_albums + total_asset_links

    @typechecked
    def classification_status(self) -> "ClassificationStatus":
        """
        Determines the classification status based on number of matched rules (lazy loaded).

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
        """Access match by index (lazy loaded)."""
        return self._get_matches()[idx]

    @typechecked
    def __len__(self) -> int:
        """Get number of matched rules (lazy loaded)."""
        return len(self._get_matches())
