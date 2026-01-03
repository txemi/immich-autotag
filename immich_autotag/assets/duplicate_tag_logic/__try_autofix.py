from typeguard import typechecked
from typing import TYPE_CHECKING
from ._classification_tag_comparison_result import _ClassificationTagComparisonResult
if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

@typechecked
def try_autofix(asset_wrapper: 'AssetResponseWrapper', duplicate_wrapper: 'AssetResponseWrapper', fix_type: _ClassificationTagComparisonResult, tag_to_add: str, verbose: bool) -> None:
    """
    Realiza el autofix de etiquetas de clasificación entre duplicados.
    """
    from immich_autotag.logging.utils import log
    from immich_autotag.logging.levels import LogLevel
    if fix_type == _ClassificationTagComparisonResult.AUTOFIX_OTHER:
        duplicate_wrapper.add_tag_by_name(tag_to_add, verbose=verbose)
        log(f"[DUPLICATE TAGS][AUTO-FIX] Añadida etiqueta de clasificación '{tag_to_add}' a asset {duplicate_wrapper.asset.id}", level=LogLevel.FOCUS)
    elif fix_type == _ClassificationTagComparisonResult.AUTOFIX_SELF:
        asset_wrapper.add_tag_by_name(tag_to_add, verbose=verbose)
        log(f"[DUPLICATE TAGS][AUTO-FIX] Añadida etiqueta de clasificación '{tag_to_add}' a asset {asset_wrapper.asset.id}", level=LogLevel.FOCUS)
    else:
        raise ValueError(f"Tipo de autofix desconocido: {fix_type}")
