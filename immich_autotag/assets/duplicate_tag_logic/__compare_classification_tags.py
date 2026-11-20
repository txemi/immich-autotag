from typing import TYPE_CHECKING, Set

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from ._classification_tag_comparison_result import ClassificationTagComparisonResult
from ._classification_tag_comparison_result_obj import (
    ClassificationTagComparisonResultObj,
)


def _matched_rule_keys(asset: "AssetResponseWrapper") -> frozenset[int]:
    """Identity of the configured classification rules the asset matches.

    A rule counts whether it matched through a tag or through an album.
    """
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )

    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    return frozenset(
        id(match.rule().rule)
        for match in rule_set.matching_rules(asset).rules()
        if match.has_match()
    )


@typechecked
def compare_classification_tags(
    asset1: "AssetResponseWrapper", asset2: "AssetResponseWrapper"
) -> ClassificationTagComparisonResultObj:
    """
    Compares the classification tags of two assets.
    Returns ("equal", None), ("autofix_other", tag), ("autofix_self", tag) or ("conflict", (tags1, tags2)).
    """
    # Two duplicates that match the same classification rules are classified
    # alike, even if one matches through a tag and the other through an album
    # (a MOVE conversion took the tag off one and put it in the album).
    # Comparing tags only made them pass the tag back and forth on every run.
    rules1 = _matched_rule_keys(asset1)
    if rules1 and rules1 == _matched_rule_keys(asset2):
        return ClassificationTagComparisonResultObj(
            ClassificationTagComparisonResult.EQUAL, None
        )
    tags1: Set[str] = set(asset1.get_classification_tags())
    tags2: Set[str] = set(asset2.get_classification_tags())
    if tags1 == tags2:
        return ClassificationTagComparisonResultObj(
            ClassificationTagComparisonResult.EQUAL, None
        )
    if tags1 and not tags2 and len(tags1) == 1:
        return ClassificationTagComparisonResultObj(
            ClassificationTagComparisonResult.AUTOFIX_OTHER, next(iter(tags1))
        )
    if tags2 and not tags1 and len(tags2) == 1:
        return ClassificationTagComparisonResultObj(
            ClassificationTagComparisonResult.AUTOFIX_SELF, next(iter(tags2))
        )
    return ClassificationTagComparisonResultObj(
        ClassificationTagComparisonResult.CONFLICT, (tags1, tags2)
    )
