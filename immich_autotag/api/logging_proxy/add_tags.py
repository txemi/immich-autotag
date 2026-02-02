"""
Logging proxy for adding tags to assets.

Wraps immich_proxy.tags.proxy_tag_assets to add automatic event logging,
error handling, and modification reporting.

This layer receives rich wrapper objects (TagWrapper, etc.) instead of
raw IDs and names. This ensures robust, type-safe operations with full
context available for event tracking and error handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.api.immich_proxy.tags import proxy_tag_assets as _proxy_tag_assets
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.tags.tag_response_wrapper import TagWrapper
    from immich_autotag.types.client_types import ImmichClient
    from immich_autotag.types.uuid_wrappers import AssetUUID

logger = logging.getLogger(__name__)


@typechecked
def logging_tag_assets(
    *,
    client: ImmichClient,
    tag: TagWrapper,
    asset_ids: list[AssetUUID],
) -> None:
    """
    Add a tag to multiple assets with automatic event logging.

    Args:
        client: Immich client instance
        tag: TagWrapper object containing tag information
        asset_ids: List of AssetUUID objects to tag

    Side effects:
        - Calls the API to tag the assets
        - Records individual events in ModificationReport for each asset
        - Updates statistics (delegated to ModificationReport)
        - Logs the action

    Note:
        A separate ADD_TAG_TO_ASSET event is recorded for each asset.
    """
    tag_id = tag.get_id()
    tag_name = tag.get_name()

    # Call the underlying proxy function
    _proxy_tag_assets(client=client, tag_id=tag_id, asset_ids=asset_ids)

    # Record events in the modification report
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    for asset_id in asset_ids:
        report.add_tag_modification(
            kind=ModificationKind.ADD_TAG_TO_ASSET,
            tag=tag,
        )

    # Log the action
    logger.info(
        f"[TAG_ASSETS] Tag '{tag_name}' (id={tag_id}) added to "
        f"{len(asset_ids)} asset(s)"
    )


@typechecked
def logging_tag_assets_safe(
    *,
    client: ImmichClient,
    tag: TagWrapper,
    asset_ids: list[AssetUUID],
) -> list[ModificationEntry]:
    """
    Add a tag to multiple assets with automatic event logging and error handling.

    Returns list of ModificationEntry objects created for this operation.
    Entries are automatically added to the ModificationReport singleton.

    Args:
        client: Immich client instance
        tag: TagWrapper object containing tag information
        asset_ids: List of AssetUUID objects to tag

    Returns:
        list[ModificationEntry]: All entries created for this operation (empty if error)

    Side effects:
        - Calls the API to tag the assets
        - Records the operation in ModificationReport singleton
        - Updates statistics (delegated to ModificationReport)
        - Logs actions and errors
    """
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.report.modification_report import ModificationReport

    tag_id = tag.get_id()
    tag_name = tag.get_name()
    report = ModificationReport.get_instance()
    prev_count = len(report.modifications)

    try:
        # Call the underlying proxy function
        _proxy_tag_assets(client=client, tag_id=tag_id, asset_ids=asset_ids)

        # Record success events in the modification report
        for asset_id in asset_ids:
            report.add_tag_modification(
                kind=ModificationKind.ADD_TAG_TO_ASSET,
                tag=tag,
            )

        # Log the action
        logger.info(
            f"[TAG_ASSETS] Tag '{tag_name}' (id={tag_id}) added to "
            f"{len(asset_ids)} asset(s)"
        )

        # Return all entries created in this operation
        return report.modifications[prev_count:]

    except Exception as e:
        error_msg = f"[ERROR] Exception during proxy_tag_assets: {e}"
        log(error_msg, level=LogLevel.ERROR)

        # Record failure in modification report
        report.add_tag_modification(
            kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
            tag=tag,
        )
        # Return the failure entry(ies)
        return report.modifications[prev_count:]
