"""
Logging proxy for creating tags.

Wraps immich_proxy.tags.proxy_create_tag to add automatic event logging,
error handling, and modification reporting.

This layer receives tag names and returns rich wrapper objects (TagWrapper)
to ensure robust, type-safe operations with full context available for
event tracking and error handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from typeguard import typechecked

from immich_autotag.report.modification_entry import ModificationEntry

if TYPE_CHECKING:
    from immich_autotag.types.client_types import ImmichClient

logger = logging.getLogger(__name__)


@typechecked
def logging_create_tag(
    *,
    client: ImmichClient,
    name: str,
) -> ModificationEntry:
    """
    Create a tag with automatic event logging and modification tracking.

    Args:
        client: Immich client instance
        name: Name of the tag to create

    Returns:
        ModificationEntry: The report entry containing the tag wrapper and operation details

    Side effects:
        - Calls the API to create the tag
        - Records the event in ModificationReport
        - Updates statistics (delegated to ModificationReport)
        - Logs the creation event

    Note:
        This function encapsulates the complete lifecycle: API call, wrapping,
        and reporting. The returned ModificationEntry contains the TagWrapper
        in its tag attribute, eliminating the need to return both separately.
    """
    from immich_autotag.api.immich_proxy.tags import (
        proxy_create_tag as _proxy_create_tag,
    )
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.report.modification_report import ModificationReport
    from immich_autotag.tags.tag_response_wrapper import TagWrapper

    # Call the underlying proxy function to create the tag
    new_tag_dto = _proxy_create_tag(client=client, name=name)

    if new_tag_dto is None:
        raise RuntimeError(f"Failed to create tag '{name}': API returned None")

    # Wrap the DTO for type safety and consistency
    from immich_autotag.tags.tag_response_wrapper import TagSource
    tag_wrapper = TagWrapper(new_tag_dto, TagSource.CREATE_TAG)

    # Record the event in the modification report
    report = ModificationReport.get_instance()
    entry = report.add_tag_modification(
        kind=ModificationKind.CREATE_TAG,
        tag=tag_wrapper,
    )

    # Log the creation
    logger.info(f"[CREATE_TAG] Created tag: '{name}' (id={tag_wrapper.get_id()})")

    return entry
