from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def mark_and_log_conflict(asset_wrapper: "AssetResponseWrapper") -> None:
    """
    Marks and logs the classification tag conflict between duplicates.
    """
    from immich_autotag.config.manager import ConfigManager
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    from .__get_duplicate_wrappers import get_duplicate_wrappers

    duplicate_wrappers = get_duplicate_wrappers(asset_wrapper)
    details = [w.format_info() for w in duplicate_wrappers]
    msg = (
        "[DUPLICATE TAGS][CONFLICT] Classification tags differ for duplicates. Detailed information of all involved:\n"
        + "\n".join(details)
    )
    log(msg, level=LogLevel.FOCUS)
    from immich_autotag.config.models import DuplicateProcessingConfig, UserConfig

    config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
    if config.duplicate_processing is None:
        log(
            "[DUPLICATE TAGS][CONFLICT] duplicate_processing missing, cannot tag conflict.",
            level=LogLevel.ERROR,
        )
        return
    duplicate_processing: DuplicateProcessingConfig = config.duplicate_processing

    from immich_autotag.types.uuid_wrappers import DuplicateUUID
    duplicate_id: DuplicateUUID = asset_wrapper.get_duplicate_id_as_uuid()
    group_tag = f"{duplicate_processing.autotag_classification_conflict_prefix}{duplicate_id}"
    for w in duplicate_wrappers:
        if duplicate_processing.autotag_classification_conflict is not None:
            w.add_tag_by_name(
                tag_name=duplicate_processing.autotag_classification_conflict
            )
        w.add_tag_by_name(tag_name=group_tag)
