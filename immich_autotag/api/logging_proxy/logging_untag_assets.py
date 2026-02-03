"""
Remove a tag from multiple assets with automatic event logging and error handling.

This is the safe, public logging-proxy entrypoint for untagging assets.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from typeguard import typechecked
import logging

from immich_autotag.api.immich_proxy.tags import proxy_untag_assets as _proxy_untag_assets
from immich_autotag.report.modification_kind import ModificationKind

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_entries_list import ModificationEntriesList
    from immich_autotag.report.modification_entry import ModificationEntry
    from immich_autotag.tags.tag_response_wrapper import TagWrapper
    from immich_autotag.types.client_types import ImmichClient

logger = logging.getLogger(__name__)

@typechecked
def logging_untag_assets_safe(
    *,
    client: 'ImmichClient',
    tag: 'TagWrapper',
    asset_wrappers: list['AssetResponseWrapper'],
) -> 'ModificationEntriesList':
    """
    Remove a tag from assets with error handling.
    Returns ModificationEntriesList for this operation.
    Entries are automatically added to the ModificationReport singleton.
    """
    from immich_autotag.report.modification_entries_list import (
        ModificationEntriesList,
    )
    from immich_autotag.report.modification_report import ModificationReport

    report = ModificationReport.get_instance()

    try:
        entries = _logging_untag_assets(
            client=client, tag=tag, asset_wrappers=asset_wrappers
        )
        return ModificationEntriesList(entries=entries)
    except Exception as e:
        logger.error(
            f"Failed to remove tag '{tag.get_name()}' from {len(asset_wrappers)} "
            f"asset(s): {str(e)}"
        )
        entry = report.add_tag_modification(
            kind=ModificationKind.WARNING_TAG_REMOVAL_FROM_ASSET_FAILED,
            tag=tag,
        )
        return ModificationEntriesList(entries=[entry])

@typechecked
def _logging_untag_assets(
    *,
    client: 'ImmichClient',
    tag: 'TagWrapper',
    asset_wrappers: list['AssetResponseWrapper'],
) -> list['ModificationEntry']:
    tag_id = tag.get_id()
    tag_name = tag.get_name()
    asset_ids = [asset.get_id() for asset in asset_wrappers]
    _proxy_untag_assets(client=client, tag_id=tag_id, asset_ids=asset_ids)
    from immich_autotag.report.modification_report import ModificationReport
    report = ModificationReport.get_instance()
    entries: list['ModificationEntry'] = []
    for asset_wrapper in asset_wrappers:
        entry = report.add_tag_modification(
            kind=ModificationKind.REMOVE_TAG_FROM_ASSET,
            tag=tag,
            asset_wrapper=asset_wrapper,
        )
        entries.append(entry)
    logger.info(
        f"[UNTAG_ASSETS] Tag '{tag_name}' (id={tag_id}) removed from "
        f"{len(asset_wrappers)} asset(s)"
    )
    return entries
