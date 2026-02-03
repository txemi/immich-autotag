from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.assets.albums._process_album_detection import (
    process_album_detection,
)
from immich_autotag.assets.albums.album_decision import AlbumDecision
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult
from immich_autotag.classification.classification_rule_set import (
    ClassificationRuleSet,
)
from immich_autotag.classification.classification_status import ClassificationStatus
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport

if TYPE_CHECKING:
    from immich_autotag.classification.match_result_list import MatchResultList


class AlbumAssignmentResult(Enum):
    CLASSIFIED = auto()
    CONFLICT = auto()
    ASSIGNED_UNIQUE = auto()
    CREATED_TEMPORARY = auto()
    UNCLASSIFIED_NO_ALBUM = auto()
    ERROR = auto()


@typechecked
def _handle_duplicate_conflicts(
    asset_wrapper: AssetResponseWrapper, album_decision: AlbumDecision
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


@typechecked
def _handle_classified_asset(
    asset_wrapper: AssetResponseWrapper, tag_mod_report: ModificationReport
) -> AlbumAssignmentResult:
    """
    Cleans up temporary albums and updates tags for a classified asset.
    """
    from immich_autotag.assets.albums.temporary_manager.cleanup import (
        remove_asset_from_autotag_temporary_albums,
    )

    all_albums = list(
        asset_wrapper.get_context()
        .get_albums_collection()
        .albums_wrappers_for_asset_wrapper(asset_wrapper)
    )
    remove_asset_from_autotag_temporary_albums(
        asset_wrapper=asset_wrapper,
        temporary_albums=all_albums,
        tag_mod_report=tag_mod_report,
    )

    # Remove 'unknown' tag if present and update classification tags
    asset_wrapper.validate_and_update_classification()

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_wrapper.get_original_file_name()}' classified. "
        f"Temporary album cleanup and tags updated.",
        level=LogLevel.FOCUS,
    )
    return AlbumAssignmentResult.CLASSIFIED


@typechecked
def _handle_classification_conflict(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
    match_results: "MatchResultList",
) -> AlbumAssignmentResult:
    """
    Handles assets that match multiple classification rules by removing them from temporary albums
    and reporting the conflict.
    """
    from immich_autotag.assets.albums.temporary_manager.cleanup import (
        remove_asset_from_autotag_temporary_albums,
    )

    all_albums = list(
        asset_wrapper.get_context()
        .get_albums_collection()
        .albums_wrappers_for_asset_wrapper(asset_wrapper)
    )
    remove_asset_from_autotag_temporary_albums(
        asset_wrapper=asset_wrapper,
        temporary_albums=all_albums,
        tag_mod_report=tag_mod_report,
    )

    num_rules_matched = len(list(match_results.rules()))
    asset_name = asset_wrapper.get_original_file_name()
    asset_id = asset_wrapper.get_id()
    immich_url = asset_wrapper.get_immich_photo_url().geturl()

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_name}' ({asset_id}) matched {num_rules_matched} classification rules. "
        f"Classification conflict: removed from temporary album if it was there.\nSee asset: {immich_url}",
        level=LogLevel.ERROR,
    )

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
    return AlbumAssignmentResult.CONFLICT


@typechecked
def _handle_unclassified_asset(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
    album_decision: AlbumDecision,
) -> AlbumAssignmentResult:
    """
    Attempts to assign an album to an unclassified asset via detection or temporary album creation.
    """
    asset_name = asset_wrapper.get_original_file_name()

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
                asset_wrapper=asset_wrapper,
                tag_mod_report=tag_mod_report,
                detected_album=detected_album,
                album_origin=album_origin,
            )
            return AlbumAssignmentResult.ASSIGNED_UNIQUE

    # If no unique album detected, try to create a temporary album
    from immich_autotag.assets.albums.temporary_manager.create_if_missing_classification import (
        create_album_if_missing_classification,
    )

    created_album = create_album_if_missing_classification(
        asset_wrapper, tag_mod_report
    )
    if created_album:
        return AlbumAssignmentResult.CREATED_TEMPORARY

    log(
        f"[ALBUM ASSIGNMENT] Asset '{asset_name}' is not classified and no album could be assigned.",
        level=LogLevel.DEBUG,
    )
    return AlbumAssignmentResult.UNCLASSIFIED_NO_ALBUM


@typechecked
def _analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> AlbumAssignmentResult:
    """
    Handles all logic related to analyzing potential albums for an asset, deciding assignment, and handling conflicts.
    """
    album_decision = AlbumDecision(asset_wrapper=asset_wrapper)

    # 1. Handle duplicate conflicts
    _handle_duplicate_conflicts(asset_wrapper, album_decision)

    # 2. Check classification status
    rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
    match_results = rule_set.matching_rules(asset_wrapper)
    status = match_results.classification_status()

    # 3. Handle based on status
    if status == ClassificationStatus.CLASSIFIED:
        return _handle_classified_asset(asset_wrapper, tag_mod_report)

    if status == ClassificationStatus.CONFLICT:
        return _handle_classification_conflict(
            asset_wrapper, tag_mod_report, match_results
        )

    if status == ClassificationStatus.UNCLASSIFIED:
        return _handle_unclassified_asset(asset_wrapper, tag_mod_report, album_decision)

    # Exhaustive pattern match - should never reach here
    raise NotImplementedError(
        f"Unhandled classification status: {status}. This indicates a logic error in ClassificationStatus enum."
    )


@attrs.define(auto_attribs=True, slots=True)
class AlbumAssignmentReport(ProcessStepResult):
    """
    Manages album assignment logic for assets based on their classification status.

    This class orchestrates the complete album assignment workflow:
    - For classified assets: removes them from temporary albums and updates classification tags
    - For conflicted assets: removes from temporary albums and logs the conflict
    - For unclassified assets: attempts album detection (from folders/duplicates) or creates temporary album

    The assignment logic handles:
    1. Detection of album conflicts across duplicate assets
    2. Classification status evaluation (CLASSIFIED, CONFLICT, UNCLASSIFIED)
    3. Temporary album cleanup when asset gets classified
    4. Album detection from folder structure or duplicate asset information
    5. Creation of temporary albums when no classification or detection succeeds

    This is a critical step in the asset processing pipeline as it ensures:
    - Classified assets are properly organized in their definitive albums
    - Temporary albums serve as holding areas only for unclassified assets
    - Conflicts are properly detected and reported
    - Album information is propagated across duplicate assets
    """

    _asset_wrapper: AssetResponseWrapper = attrs.field(repr=False)
    _result: AlbumAssignmentResult = attrs.field(init=False, default=None, repr=True)

    def has_changes(self) -> bool:
        return self._result in (
            AlbumAssignmentResult.CLASSIFIED,
            AlbumAssignmentResult.ASSIGNED_UNIQUE,
            AlbumAssignmentResult.CREATED_TEMPORARY,
        )

    def has_errors(self) -> bool:
        return self._result in (
            AlbumAssignmentResult.CONFLICT,
            AlbumAssignmentResult.ERROR,
        )

    def get_title(self) -> str:
        return "Album assignment logic"

    def format(self) -> str:
        return f"ALBUM_ASSIGNMENT ({self._result.name})"

    @classmethod
    def analyze(
        cls,
        asset_wrapper: AssetResponseWrapper,
        tag_mod_report: ModificationReport,
    ) -> "AlbumAssignmentReport":
        report = cls(asset_wrapper=asset_wrapper)
        report._perform_analysis(tag_mod_report)
        return report

    def _perform_analysis(self, tag_mod_report: ModificationReport) -> None:
        self._result = _analyze_and_assign_album(self._asset_wrapper, tag_mod_report)


@typechecked
def analyze_and_assign_album(
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> AlbumAssignmentReport:
    return AlbumAssignmentReport.analyze(asset_wrapper, tag_mod_report)
