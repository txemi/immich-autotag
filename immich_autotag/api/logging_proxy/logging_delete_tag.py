"""
Delete a tag globally with automatic event logging and statistics tracking.

This is the public logging-proxy entrypoint for deleting a tag from the system.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from typeguard import typechecked
from immich_autotag.api.immich_proxy.tags import proxy_delete_tag as _proxy_delete_tag
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.tags.tag_response_wrapper import TagWrapper
    from immich_autotag.types.client_types import ImmichClient
    from immich_autotag.report.modification_entry import ModificationEntry

@typechecked
def logging_delete_tag(
    *,
    client: 'ImmichClient',
    tag: 'TagWrapper',
    reason: Optional[str] = None,
) -> 'ModificationEntry':
    """
    Delete a tag with automatic event logging and statistics tracking.
    """
    tag_id = tag.get_id()
    _proxy_delete_tag(client=client, tag_id=tag_id)
    from immich_autotag.report.modification_report import ModificationReport
    report = ModificationReport.get_instance()
    entry = report.add_tag_modification(
        kind=ModificationKind.REMOVE_TAG_GLOBALLY,
        tag=tag,
    )
    return entry
