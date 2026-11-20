"""Private handler for duplicate asset conflicts in album assignment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from typeguard import typechecked

from immich_autotag.report.modification_entries_list import ModificationEntriesList

if TYPE_CHECKING:
    from immich_autotag.assets.albums.album_decision import AlbumDecision
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


def _group_album_options(wrappers: Iterable["AssetResponseWrapper"]) -> set[str]:
    """Valid albums of a whole duplicate group: each copy's albums and folder album.

    The same set comes out whichever copy is being processed, so every copy of the
    group gets the same verdict. A per-copy view (the other copies' albums plus this
    copy's folder) differs from copy to copy: one copy saw a conflict and tagged the
    group, the next one saw none and untagged it, on every run.
    """
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )

    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    options: set[str] = set()
    for wrapper in wrappers:
        options.update(wrapper.get_album_names())
        folder_album = wrapper.try_detect_album_from_folders()
        if folder_album:
            options.add(folder_album)
    return {album for album in options if rule_set.matches_album(album)}


@typechecked
def handle_duplicate_conflicts(
    asset_wrapper: "AssetResponseWrapper", album_decision: "AlbumDecision"
) -> ModificationEntriesList:
    """
    Detects album conflicts across duplicate assets and applies the conflict tag logic.

    The conflict is decided once for the whole duplicate group (see
    `_group_album_options`), not from this copy's point of view.
    """
    from immich_autotag.types.uuid_wrappers import DuplicateUUID

    duplicate_id_or_none = asset_wrapper.get_duplicate_id_as_uuid()
    # If there's no duplicate ID, this asset has no duplicates - nothing to do
    if duplicate_id_or_none is None:
        return ModificationEntriesList()
    duplicate_id: DuplicateUUID = duplicate_id_or_none
    all_wrappers = [asset_wrapper] + list(
        album_decision.duplicates_info.get_details().values()
    )
    conflict = len(_group_album_options(all_wrappers)) > 1
    mods = ModificationEntriesList()
    for wrapper in all_wrappers:
        modifications = wrapper.ensure_autotag_duplicate_album_conflict(
            conflict=conflict, duplicate_id=duplicate_id
        )
        if modifications is not None:
            mods = mods.extend(modifications)
    return mods
