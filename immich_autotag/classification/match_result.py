from typing import TYPE_CHECKING

import attr
from typeguard import typechecked

from immich_autotag.classification.validators import validate_classification_rule

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.classification.classification_rule_wrapper import (
        ClassificationRuleWrapper,
    )


# Represents the result of a match: reference to the rule and the matched tags and albums
@attr.s(auto_attribs=True, slots=True, kw_only=True, frozen=True)
class MatchResult:
    _rule: "ClassificationRuleWrapper" = attr.ib(validator=validate_classification_rule, alias="rule", init=True)
    _tags_matched: list[str] = attr.ib(
        factory=list,
        validator=attr.validators.instance_of(list),
        alias="tags_matched",
    )
    _albums_matched: list[str] = attr.ib(
        factory=list,
        validator=attr.validators.instance_of(list),
        alias="albums_matched",
    )
    _asset_links_matched: list[str] = attr.ib(
        factory=list,
        validator=attr.validators.instance_of(list),
        alias="asset_links_matched",
    )
    _asset: "AssetResponseWrapper" = attr.ib(alias="asset", init=True)

    def __attrs_post_init__(self):
        if not (self._tags_matched or self._albums_matched or self._asset_links_matched):
            raise ValueError(
                "MatchResult must have at least one matching tag, album, or asset link."
            )

    @typechecked
    def rule(self) -> "ClassificationRuleWrapper":
        """Returns the classification rule that produced this match."""
        return self._rule

    @typechecked
    def tags_matched(self) -> list[str]:
        """Returns the list of tags matched by this rule."""
        return self._tags_matched

    @typechecked
    def albums_matched(self) -> list[str]:
        """Returns the list of albums matched by this rule."""
        return self._albums_matched

    @typechecked
    def asset_links_matched(self) -> list[str]:
        """Returns the list of asset links matched by this rule."""
        return self._asset_links_matched

    @typechecked
    def asset(self) -> "AssetResponseWrapper":
        """Returns the asset that produced this match result."""
        return self._asset

    @typechecked
    def has_match(self) -> bool:
        """
        Returns True if there is at least one matching tag, album, or asset link in the result.
        """
        return bool(
            self._tags_matched or self._albums_matched or self._asset_links_matched
        )

    @typechecked
    def is_match(self) -> bool:
        """
        Returns True if there is at least one matching tag, album, or asset link in the result.
        """
        return bool(
            self._tags_matched or self._albums_matched or self._asset_links_matched
        )
