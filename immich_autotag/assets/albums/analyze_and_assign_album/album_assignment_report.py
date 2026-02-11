"""AlbumAssignmentReport class for album assignment processing results."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult

from ._analyze_and_assign_album import AlbumAssignmentResultInfo
from .album_assignment_result import AlbumAssignmentResult

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.report.modification_entries_list import ModificationEntriesList
    from immich_autotag.report.modification_report import ModificationReport


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

    _asset_wrapper: "AssetResponseWrapper" = attrs.field(repr=False)
    _result: AlbumAssignmentResultInfo = attrs.field(
        init=False, default=None, repr=True
    )

    def __attrs_post_init__(self):
        if self._result is not None and not isinstance(
            self._result, AlbumAssignmentResultInfo
        ):
            raise TypeError(
                f"_result must be AlbumAssignmentResultInfo, got {type(self._result)}"
            )
        # Integrity check: ensure the asset in _result matches the asset in this report
        # This is intended to allow future removal of the _asset_wrapper attribute
        if self._result is not None:
            # Direct attribute access: AlbumAssignmentResultInfo always has .asset
            result_asset = self._result.get_unique_asset()
            if result_asset is not None and result_asset is not self._asset_wrapper:
                raise ValueError(
                    "Integrity check failed: asset in _result does not match asset in AlbumAssignmentReport. "
                    "This exception is intentional and documents the future plan to remove the _asset_wrapper attribute."
                )

    def has_changes(self) -> bool:
        modifications = self._result.get_modifications()
        if modifications is not None and modifications.has_changes():
            return True
        if self._result.get_result() in (
            AlbumAssignmentResult.ASSIGNED_UNIQUE,
            AlbumAssignmentResult.CREATED_TEMPORARY,
        ):
            return True
        return False

    def has_errors(self) -> bool:
        modifications = self._result.get_modifications()
        if modifications is not None and modifications.has_errors():
            return True
        if self._result.get_result() in (AlbumAssignmentResult.ERROR,):
            return True
        return False

    def get_title(self) -> str:
        return "Album assignment logic"

    def get_events(self) -> "ModificationEntriesList":
        """Returns events from album assignment (empty, as assignment doesn't track modification events)."""
        from immich_autotag.report.modification_entries_list import (
            ModificationEntriesList,
        )

        return ModificationEntriesList()

    def format(self) -> str:
        return self._result.format_assignment()

    @classmethod
    def analyze(
        cls,
        asset_wrapper: "AssetResponseWrapper",
        tag_mod_report: "ModificationReport",
    ) -> "AlbumAssignmentReport":
        report = cls(asset_wrapper=asset_wrapper)
        report._perform_analysis(tag_mod_report)
        return report

    def _perform_analysis(self, tag_mod_report: "ModificationReport") -> None:
        from ._analyze_and_assign_album import analyze_and_assign_album

        self._result = analyze_and_assign_album(self._asset_wrapper, tag_mod_report)
