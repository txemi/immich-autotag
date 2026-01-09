from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from .__compare_classification_tags import compare_classification_tags
from .__get_duplicate_wrappers import get_duplicate_wrappers
from .__mark_and_log_conflict import mark_and_log_conflict
from .__try_autofix import try_autofix
from ._classification_tag_comparison_result import ClassificationTagComparisonResult


@typechecked
def analyze_duplicate_classification_tags(
    asset_wrapper: AssetResponseWrapper,
) -> None:
    """
    Checks the classification tags of all duplicates of the given asset.
    - If tags are equal, does nothing.
    - If tags can be autofixed, attempts autofix.
    - If there is a conflict, marks and logs the conflict.
    - Does not raise exceptions; only logs and marks conflicts.
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    duplicate_id = asset_wrapper.asset.duplicate_id
    if not duplicate_id:
        log(
            f"[DUPLICATE TAGS] Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name}) has no duplicates. Nothing to check.",
            level=LogLevel.FOCUS,
        )
        return
    duplicate_wrappers = get_duplicate_wrappers(asset_wrapper)
    any_autofix = False
    for duplicate_wrapper in duplicate_wrappers:
        if duplicate_wrapper.asset.id == asset_wrapper.asset.id:
            continue
        log(
            f"[DUPLICATE TAGS][INFO] Duplicate asset info:\n{duplicate_wrapper.format_info()}",
            level=LogLevel.FOCUS,
        )
        comp_result = compare_classification_tags(asset_wrapper, duplicate_wrapper)
        if comp_result.result == ClassificationTagComparisonResult.EQUAL:
            continue
        elif comp_result.result in (
            ClassificationTagComparisonResult.AUTOFIX_OTHER,
            ClassificationTagComparisonResult.AUTOFIX_SELF,
        ):
            if comp_result.tag_info is not None:
                try_autofix(
                    asset_wrapper,
                    duplicate_wrapper,
                    comp_result.result,
                    comp_result.tag_info,
                )
                any_autofix = True
            else:
                log(
                    f"[DUPLICATE TAGS][ERROR] tag_info is None for autofix result on asset {asset_wrapper.asset.id}",
                    level=LogLevel.ERROR,
                )
            continue
        elif comp_result.result == ClassificationTagComparisonResult.CONFLICT:
            mark_and_log_conflict(asset_wrapper)
            return
    if not any_autofix:
        log(
            f"[DUPLICATE TAGS] No classification tag changes were made for asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})",
            level=LogLevel.FOCUS,
        )
