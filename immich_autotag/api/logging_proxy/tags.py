"""
Logging proxy for tag operations.

Wraps immich_proxy.tags functions to add automatic event logging,
statistics tracking, and modification reporting.

This layer receives rich wrapper objects (TagWrapper, etc.) instead of
raw IDs and names. This ensures robust, type-safe operations with full
context available for event tracking and error handling.

Design: The ModificationReport is the single source of truth for all logging
and event tracking. This layer delegates all logging responsibilities to it.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from typeguard import typechecked

from immich_autotag.api.immich_proxy.tags import proxy_create_tag as _proxy_create_tag
from immich_autotag.api.immich_proxy.tags import proxy_delete_tag as _proxy_delete_tag
from immich_autotag.api.immich_proxy.tags import proxy_tag_assets as _proxy_tag_assets
from immich_autotag.api.immich_proxy.tags import (
    proxy_untag_assets as _proxy_untag_assets,
)
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_client.models.tag_response_dto import TagResponseDto

    from immich_autotag.tags.tag_response_wrapper import TagWrapper
    from immich_autotag.types.client_types import ImmichClient
    from immich_autotag.types.uuid_wrappers import AssetUUID

logger = logging.getLogger(__name__)


@typechecked
def logging_create_tag(
    *,
    client: ImmichClient,
    name: str,
) -> TagResponseDto:
    """
    Create a tag with automatic logging.

    Args:
        client: Immich client instance
        name: Name of the tag to create

    Returns:
        The created TagResponseDto

    Side effects:
        - Calls the API to create the tag
        - Logs the action

    Note:
        Tag creation is not registered in ModificationReport because there's
        no CREATE_TAG event type defined yet. Consider adding this if needed
        for comprehensive audit tracking.
    """
    # Call the underlying proxy function
    tag_dto = _proxy_create_tag(client=client, name=name)

    if tag_dto is None:
        raise ValueError(f"Failed to create tag '{name}': API returned None")

    # Log the action
    logger.info(f"[CREATE_TAG] Tag '{name}' created (id={tag_dto.id})")

    return tag_dto


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
        f"[TAG_ASSETS] Tag '{tag_name}' (id={tag_id}) added to {len(asset_ids)} asset(s)"
    )


@typechecked
def logging_untag_assets(
    *,
    client: ImmichClient,
    tag: TagWrapper,
    asset_ids: list[AssetUUID],
) -> None:
    """
    Remove a tag from multiple assets with automatic event logging.

    Args:
        client: Immich client instance
        tag: TagWrapper object containing tag information
        asset_ids: List of AssetUUID objects to untag

    Side effects:
        - Calls the API to untag the assets
        - Records individual events in ModificationReport for each asset
        - Updates statistics (delegated to ModificationReport)
        - Logs the action

    Note:
        A separate REMOVE_TAG_FROM_ASSET event is recorded for each asset.
    """
    tag_id = tag.get_id()
    tag_name = tag.get_name()

    # Call the underlying proxy function
    _proxy_untag_assets(client=client, tag_id=tag_id, asset_ids=asset_ids)

    # Record events in the modification report
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    for asset_id in asset_ids:
        report.add_tag_modification(
            kind=ModificationKind.REMOVE_TAG_FROM_ASSET,
            tag=tag,
        )

    # Log the action
    logger.info(
        f"[UNTAG_ASSETS] Tag '{tag_name}' (id={tag_id}) removed from {len(asset_ids)} asset(s)"
    )


@typechecked
def logging_delete_tag(
    *,
    client: ImmichClient,
    tag: TagWrapper,
    reason: Optional[str] = None,
) -> None:
    """
    Delete a tag with automatic event logging and statistics tracking.

    Args:
        client: Immich client instance
        tag: TagWrapper object containing tag information
        reason: Optional reason for deletion (e.g., "cleanup", "conflict_resolution")

    Side effects:
        - Calls the API to delete the tag
        - Records the event in ModificationReport with full tag context
        - Updates statistics (delegated to ModificationReport)
        - Logs the action (delegated to ModificationReport)

    Benefits of receiving TagWrapper:
        - Full tag information always available
        - Type-safe operations with no missing data
        - Consistent with ModificationReport architecture (works with wrapper objects)
        - Reduces error-prone parameter passing
        - Single source of truth for logging via ModificationReport
    """
    tag_id = tag.get_id()

    # Call the underlying proxy function
    _proxy_delete_tag(client=client, tag_id=tag_id)

    # Record the event in the modification report with full wrapper context
    # ModificationReport handles: logging, statistics, and event persistence
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()
    report.add_tag_modification(
        kind=ModificationKind.REMOVE_TAG_GLOBALLY,
        tag=tag,
    )
