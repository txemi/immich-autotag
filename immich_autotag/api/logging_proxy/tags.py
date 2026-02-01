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

from typing import TYPE_CHECKING, Optional

from typeguard import typechecked

from immich_autotag.api.immich_proxy.tags import (
    proxy_create_tag as _proxy_create_tag,
    proxy_delete_tag as _proxy_delete_tag,
)
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper
    from immich_autotag.types.client_types import ImmichClient
    from immich_client.models.tag_response_dto import TagResponseDto


@typechecked
def logging_create_tag(
    *,
    client: ImmichClient,
    name: str,
) -> TagResponseDto:
    """
    Create a tag with automatic event logging and statistics tracking.

    Args:
        client: Immich client instance
        name: Name of the tag to create

    Returns:
        The created TagResponseDto

    Side effects:
        - Calls the API to create the tag
        - Records the event in ModificationReport
        - Updates statistics (delegated to ModificationReport)
        - Logs the action (delegated to ModificationReport)
    """
    # Call the underlying proxy function
    tag_dto = _proxy_create_tag(client=client, name=name)

    if tag_dto is None:
        raise ValueError(f"Failed to create tag '{name}': API returned None")

    # Record the event in the modification report
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

    report = ModificationReport.get_instance()
    tag_wrapper = TagWrapper(tag_dto)
    report.add_tag_modification(
        kind=ModificationKind.ADD_TAG_TO_ASSET,
        tag=tag_wrapper,
    )

    return tag_dto


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
