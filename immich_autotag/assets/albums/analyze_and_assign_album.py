from __future__ import annotations

from typeguard import typechecked

from immich_autotag.assets.albums._process_album_detection import (
    process_album_detection,
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

    # Determine classification status
    from immich_autotag.classification.classification_status import ClassificationStatus

    status = match_results.classification_status()

    asset_name = asset_wrapper.original_file_name
    asset_id = asset_wrapper.id
    immich_url = asset_wrapper.get_immich_photo_url().geturl()

    if status == ClassificationStatus.CLASSIFIED:
        # Always clean up: remove from temporary albums and update classification tags
        from immich_autotag.assets.albums.temporary_manager.cleanup import (
            remove_asset_from_autotag_temporary_albums,
        )

        all_albums = list(
            asset_wrapper.context.albums_collection.albums_wrappers_for_asset_wrapper(
                asset_wrapper
            )
        )
        remove_asset_from_autotag_temporary_albums(
            asset_wrapper=asset_wrapper,
            temporary_albums=all_albums,
            tag_mod_report=tag_mod_report,
        )
        # Remove 'unknown' tag if present and update classification tags
        _ = asset_wrapper.validate_and_update_classification()
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' classified. Temporary album cleanup and tags updated.",
            level=LogLevel.FOCUS,
        )
        return

    elif status == ClassificationStatus.CONFLICT:
        # If there is a conflict, remove from all temporary/autotag albums
        from immich_autotag.assets.albums.remove_from_autotag_albums import (
            remove_asset_from_autotag_temporary_albums,
        )

        all_albums = list(
            asset_wrapper.context.albums_collection.albums_wrappers_for_asset_wrapper(
                asset_wrapper
            )
        )
        remove_asset_from_autotag_temporary_albums(
            asset_wrapper=asset_wrapper,
            temporary_albums=all_albums,
            tag_mod_report=tag_mod_report,
        )
        num_rules_matched = len(list(match_results.rules()))
        log(
            f"[ALBUM ASSIGNMENT] Asset '{asset_name}' ({asset_id}) matched {num_rules_matched} classification rules. "
            f"Classification conflict: removed from temporary album if it was there.\nSee asset: {immich_url}",
            level=LogLevel.ERROR,
        )
        # Register this in the modification report for auditing
        from immich_autotag.tags.modification_kind import ModificationKind

        tag_mod_report.add_modification(
            kind=ModificationKind.CLASSIFICATION_CONFLICT,
            asset_wrapper=asset_wrapper,
            extra={
                "reason": "multiple_rules_matched",
                "num_rules": num_rules_matched,
                "asset_name": asset_name,
                "asset_id": asset_id,
            },
        )
        return

    elif status == ClassificationStatus.UNCLASSIFIED:
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
                process_album_detection(
                    asset_wrapper,
                    tag_mod_report,
                    detected_album,
                    album_origin,
                )
                return

        # If no unique album detected, try to create a temporary album
        from immich_autotag.assets.albums.temporary_manager.create_if_missing_classification import (
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

    else:
        # Exhaustive pattern match - should never reach here
        raise NotImplementedError(
            f"Unhandled classification status: {status}. This indicates a logic error in ClassificationStatus enum."
        )
