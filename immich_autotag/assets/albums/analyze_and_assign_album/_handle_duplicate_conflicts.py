"""Private handler for duplicate asset conflicts in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typeguard import typechecked

if TYPE_CHECKING:
    from immich_autotag.assets.albums.album_decision import AlbumDecision
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@typechecked
def _handle_duplicate_conflicts(
    asset_wrapper: "AssetResponseWrapper", album_decision: "AlbumDecision"
) -> None:
    """
    Detects album conflicts across duplicate assets and applies the conflict tag logic.
    """
    conflict = album_decision.has_conflict()
    from immich_autotag.types.uuid_wrappers import DuplicateUUID

    duplicate_id_or_none = asset_wrapper.get_duplicate_id_as_uuid()
    # duplicate_id is always a UUID in this context; no need to check for None/Unset
    assert duplicate_id_or_none is not None
    duplicate_id: DuplicateUUID = duplicate_id_or_none
    all_wrappers = [asset_wrapper] + list(
        album_decision.duplicates_info.get_details().values()
    )
    for wrapper in all_wrappers:
        wrapper.ensure_autotag_duplicate_album_conflict(
            conflict=conflict, duplicate_id=duplicate_id
        )
