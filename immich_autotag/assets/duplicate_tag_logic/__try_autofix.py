from typing import TYPE_CHECKING

from typeguard import typechecked

from ._classification_tag_comparison_result import ClassificationTagComparisonResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def try_autofix(
    asset_wrapper: "AssetResponseWrapper",
    duplicate_wrapper: "AssetResponseWrapper",
    fix_type: "ClassificationTagComparisonResult",
    tag_to_add: str,
) -> None:
    """
    Performs autofix of classification tags between duplicates.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    if fix_type == ClassificationTagComparisonResult.AUTOFIX_OTHER:
        duplicate_wrapper.add_tag_by_name(tag_to_add)
        log(
            f"[DUPLICATE TAGS][AUTO-FIX] Added classification tag '{tag_to_add}' to asset {duplicate_wrapper.asset.id}",
            level=LogLevel.FOCUS,
        )
    elif fix_type == ClassificationTagComparisonResult.AUTOFIX_SELF:
        asset_wrapper.add_tag_by_name(tag_to_add)
        log(
            f"[DUPLICATE TAGS][AUTO-FIX] Added classification tag '{tag_to_add}' to asset {asset_wrapper.asset.id}",
            level=LogLevel.FOCUS,
        )
    else:
        raise ValueError(f"Unknown autofix type: {fix_type}")
