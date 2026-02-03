"""
Logging-proxy wrapper for asset date update event.
This module contains only the logging_update_asset_date function for architectural clarity.
"""
from immich_autotag.api.logging_proxy.types import AssetResponseDto, UpdateAssetDto
from immich_autotag.api.logging_proxy.assets import proxy_update_asset
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import is_log_level_enabled, log_debug
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.users.user_response_wrapper import UserResponseWrapper

from datetime import datetime
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.api.logging_proxy.types import AssetResponseDto, UpdateAssetDto
from typing import Any

def logging_update_asset_date(
    asset_wrapper: AssetResponseWrapper,
    new_date: datetime,
    old_date: Any,
    dto: UpdateAssetDto,
    check_update_applied: bool = False,
) -> AssetResponseDto:
    """
    Updates the asset date via proxy and logs the modification event.
    Performs type check and raises DateIntegrityError if response is not AssetResponseDto.
    """
    from immich_autotag.api.logging_proxy.assets import proxy_update_asset
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import is_log_level_enabled, log_debug
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.users.user_response_wrapper import UserResponseWrapper
    from immich_autotag.assets.asset_response_wrapper import DateIntegrityError

    if is_log_level_enabled(LogLevel.DEBUG):
        photo_url_obj = asset_wrapper.get_immich_photo_url()
        photo_url = photo_url_obj.geturl()
        log_msg = (
            f"[INFO] Updating asset date: asset.id={asset_wrapper.get_id()}, "
            f"asset_name={asset_wrapper.get_original_file_name()}, "
            f"old_date={old_date}, new_date={new_date}\n"
            f"[INFO] Immich photo link: {photo_url}"
        )
        log_debug(f"[BUG] {log_msg}")
    tag_mod_report = ModificationReport.get_instance()
    user_wrapper = UserResponseWrapper.load_current_user()
    tag_mod_report.add_modification(
        kind=ModificationKind.UPDATE_ASSET_DATE,
        asset_wrapper=asset_wrapper,
        old_value=str(old_date) if old_date else None,
        new_value=str(new_date) if new_date else None,
        user=user_wrapper,
        extra={"pre_update": True},
    )
    response = proxy_update_asset(
        asset_id=asset_wrapper.get_id(),
        client=asset_wrapper.get_context().get_client_wrapper().get_client(),
        body=dto,
    )
    if not isinstance(response, AssetResponseDto):
        raise DateIntegrityError(
            f"[ERROR] update_asset.sync did not return AssetResponseDto, "
            f"got {type(response)}: {response} for asset.id={asset_wrapper.get_id()} "
            f"({asset_wrapper.get_original_file_name()})"
        )
    if check_update_applied:
        if is_log_level_enabled(LogLevel.DEBUG):
            log_debug(f"[PERF] Date update applied: {new_date.isoformat()}")
    return response
