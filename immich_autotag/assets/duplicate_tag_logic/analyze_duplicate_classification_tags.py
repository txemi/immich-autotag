from typeguard import typechecked
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.config.user import VERBOSE_LOGGING
from .__get_duplicate_wrappers import get_duplicate_wrappers
from .__compare_classification_tags import compare_classification_tags
from .__try_autofix import try_autofix
from .__mark_and_log_conflict import mark_and_log_conflict
from ._classification_tag_comparison_result import _ClassificationTagComparisonResult

@typechecked
def analyze_duplicate_classification_tags(
    asset_wrapper: AssetResponseWrapper,
    verbose: bool = VERBOSE_LOGGING,
) -> None:
    """
    If the asset has duplicates, checks the classification tags of each duplicate.
    If the classification tags (from config) do not match, raises an exception.
    """
    from immich_autotag.logging.utils import log
    from immich_autotag.logging.levels import LogLevel
    duplicate_id = asset_wrapper.asset.duplicate_id
    if not duplicate_id:
        log(f"[DUPLICATE TAGS] Asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name}) no tiene duplicados. Nada que comprobar.", level=LogLevel.FOCUS)
        return
    duplicate_wrappers = get_duplicate_wrappers(asset_wrapper)
    any_autofix = False
    for duplicate_wrapper in duplicate_wrappers:
        if duplicate_wrapper.asset.id == asset_wrapper.asset.id:
            continue
        log(f"[DUPLICATE TAGS][INFO] Duplicate asset info:\n{duplicate_wrapper.format_info()}", level=LogLevel.FOCUS)
        result, tag_info = compare_classification_tags(asset_wrapper, duplicate_wrapper)
        if result == _ClassificationTagComparisonResult.EQUAL:
            continue
        elif result in (_ClassificationTagComparisonResult.AUTOFIX_OTHER, _ClassificationTagComparisonResult.AUTOFIX_SELF):
            try_autofix(asset_wrapper, duplicate_wrapper, result, tag_info, verbose)
            any_autofix = True
            continue
        elif result == _ClassificationTagComparisonResult.CONFLICT:
            mark_and_log_conflict(asset_wrapper, verbose)
            return
    if not any_autofix:
        log(f"[DUPLICATE TAGS] No se han realizado cambios de etiquetas de clasificación para asset {asset_wrapper.asset.id} ({asset_wrapper.original_file_name})", level=LogLevel.FOCUS)


