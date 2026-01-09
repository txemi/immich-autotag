from typing import TYPE_CHECKING, Any, Optional, Set, Tuple

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from ._classification_tag_comparison_result import ClassificationTagComparisonResult
from ._classification_tag_comparison_result_obj import (
    ClassificationTagComparisonResultObj,
)


@typechecked
def compare_classification_tags(
    asset1: "AssetResponseWrapper", asset2: "AssetResponseWrapper"
) -> ClassificationTagComparisonResultObj:
    """
    Compares the classification tags of two assets.
    Returns ("equal", None), ("autofix_other", tag), ("autofix_self", tag) or ("conflict", (tags1, tags2)).
    """
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
