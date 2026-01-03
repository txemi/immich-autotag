from typeguard import typechecked
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
@typechecked
def mark_and_log_conflict(asset_wrapper: 'AssetResponseWrapper', verbose: bool) -> None:
    """
    Marca y loguea el conflicto de etiquetas de clasificación entre duplicados.
    """
    from immich_autotag.logging.utils import log
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.config.user import (
        AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT,
        AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX)
    from .__get_duplicate_wrappers import get_duplicate_wrappers
    duplicate_wrappers = get_duplicate_wrappers(asset_wrapper)
    details = [w.format_info() for w in duplicate_wrappers]
    msg = f"[DUPLICATE TAGS][CONFLICT] Classification tags differ for duplicates. Información detallada de todos los implicados:\n" + "\n".join(details)
    log(msg, level=LogLevel.FOCUS)
    group_tag = f"{AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT_PREFIX}{asset_wrapper.duplicate_id_as_uuid}"
    for w in duplicate_wrappers:
        w.add_tag_by_name(AUTOTAG_DUPLICATE_ASSET_CLASSIFICATION_CONFLICT, verbose=verbose)
        w.add_tag_by_name(group_tag, verbose=verbose)


