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
        f"[DUPLICATE TAGS][CONFLICT] Classification tags differ for duplicates. Detailed information of all involved:\n"
        + "\n".join(details)
    )
    log(msg, level=LogLevel.FOCUS)
    config = ConfigManager.get_instance().config
    group_tag = f"{config.auto_tags.duplicate_asset_classification_conflict_prefix}{asset_wrapper.duplicate_id_as_uuid}"
    for w in duplicate_wrappers:
        w.add_tag_by_name(config.auto_tags.duplicate_asset_classification_conflict)
        w.add_tag_by_name(group_tag)
