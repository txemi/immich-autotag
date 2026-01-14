from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums._process_album_detection import (
    _process_album_detection,
)
from immich_autotag.assets.albums.album_decision import AlbumDecision
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_report import ModificationReport


@typechecked
def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
    suppress_album_already_belongs_log: bool = True,
) -> None:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    album_decision = AlbumDecision(asset_wrapper=asset_wrapper)
    # If there is an album conflict among duplicates, add the conflict tag; otherwise, remove it if present
    conflict = album_decision.has_conflict()
    duplicate_id = asset_wrapper.asset.duplicate_id
    # Handle Unset type from immich_client
    from immich_client.types import Unset

    dup_id = None if isinstance(duplicate_id, Unset) else duplicate_id
    # Apply the conflict tag logic to all duplicates
    all_wrappers = [asset_wrapper] + list(
        album_decision.duplicates_info.get_details().values()
    )
    for wrapper in all_wrappers:
        wrapper.ensure_autotag_duplicate_album_conflict(conflict, duplicate_id=dup_id)

    # Check classification status by counting matched rules
    from immich_autotag.classification.classification_rule_set import (
        ClassificationRuleSet,
    )

    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    match_results = rule_set.matching_rules(asset_wrapper)
    num_rules_matched = len(
        match_results
    )  # Total matches (if same rule matches multiple times, counts each)

    asset_name = asset_wrapper.original_file_name
    asset_id = asset_wrapper.id
    immich_url = asset_wrapper.get_immich_photo_url().geturl()

    if num_rules_matched == 1:
        # Asset already classified by exactly one rule, nothing to do
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' already classified by one rule. No action needed.",
            level=LogLevel.DEBUG,
        )
        return
    elif num_rules_matched > 1:
        # Multiple rules matched - this should not happen (conflict should have been detected earlier)
        raise RuntimeError(
            f"Asset '{asset_name}' ({asset_id}) matched {num_rules_matched} classification rules. "
            f"This indicates a configuration or logic error.\nSee asset: {immich_url}"
        )

    # If we reach here: num_rules_matched == 0
    # Asset is not classified, try to assign an album through detection logic

    # First, try to detect an existing album (from folders or duplicates)
    if album_decision.is_unique():
        detected_album = album_decision.get_unique()
        if detected_album:
            album_origin = album_decision.get_album_origin(detected_album)
            log(
                f"[ALBUM ASSIGNMENT] Asset '{asset_name}' will be assigned to album '{detected_album}' (origin: {album_origin}).",
                level=LogLevel.FOCUS,
            )
            _process_album_detection(
                asset_wrapper,
                tag_mod_report,
                detected_album,
                album_origin,
                suppress_album_already_belongs_log=suppress_album_already_belongs_log,
            )
            return

    # If no unique album detected, try to create a temporary album
    from immich_autotag.assets.albums.create_album_if_missing_classification import (
        create_album_if_missing_classification,
    )

    created_album = create_album_if_missing_classification(
        asset_wrapper, tag_mod_report
    )
    if not created_album:
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' is not classified and no album could be assigned.",
            level=LogLevel.DEBUG,
        )
