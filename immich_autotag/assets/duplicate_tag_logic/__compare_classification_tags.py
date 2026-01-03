from typeguard import typechecked
from typing import TYPE_CHECKING, Tuple, Optional, Set, Any
if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from ._classification_tag_comparison_result_obj import _ClassificationTagComparisonResultObj
from ._classification_tag_comparison_result import _ClassificationTagComparisonResult
@typechecked
def compare_classification_tags(asset1: 'AssetResponseWrapper', asset2: 'AssetResponseWrapper') -> _ClassificationTagComparisonResultObj:
    """
    Compara las etiquetas de clasificación de dos assets.
    Devuelve ("equal", None), ("autofix_other", tag), ("autofix_self", tag) o ("conflict", (tags1, tags2)).
    """
    tags1: Set[str] = set(asset1.get_classification_tags())
    tags2: Set[str] = set(asset2.get_classification_tags())
    if tags1 == tags2:
        return _ClassificationTagComparisonResultObj(_ClassificationTagComparisonResult.EQUAL, None)
    if tags1 and not tags2 and len(tags1) == 1:
        return _ClassificationTagComparisonResultObj(_ClassificationTagComparisonResult.AUTOFIX_OTHER, next(iter(tags1)))
    if tags2 and not tags1 and len(tags2) == 1:
        return _ClassificationTagComparisonResultObj(_ClassificationTagComparisonResult.AUTOFIX_SELF, next(iter(tags2)))
    return _ClassificationTagComparisonResultObj(_ClassificationTagComparisonResult.CONFLICT, (tags1, tags2))

