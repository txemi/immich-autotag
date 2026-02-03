"""
Checks for consistency between asset date and album date (from album name).
If the difference is greater than a threshold (default: 6 months), logs it in the ModificationReport.
"""

from __future__ import annotations

import re
from datetime import datetime

import attrs
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.assets.process.process_step_result_protocol import ProcessStepResult
from immich_autotag.config.manager import ConfigManager
from immich_autotag.config.models import AlbumDateConsistencyConfig
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport


@attrs.define(auto_attribs=True, slots=True)
class AlbumDateConsistencyResult(ProcessStepResult):
    """
    Checks date consistency between asset dates and album dates extracted from album names.

    This class validates that assets are in albums with matching date information.
    Albums with names in YYYY-MM-DD, YYYY-MM, or YYYY format are checked against
    the asset's best date (photo taken date, file creation date, etc.).

    The consistency check performs:
    - Extracts date from album name using regex pattern (YYYY-MM-DD format)
    - Compares album date with asset's best date
    - If difference exceeds threshold (configured in days), marks as mismatch
    - Automatically tags mismatched assets with configurable autotag
    - Removes autotag when mismatch is resolved

    This is important for:
    - Detecting incorrectly dated photos in date-based albums
    - Identifying photos that were manually moved to wrong date albums
    - Finding photos with incorrect EXIF date information
    - Maintaining temporal consistency in album organization

    Note: This check focuses on date consistency, while DuplicateTagAnalysisReport
    handles classification consistency across duplicate assets.
    """

    _asset_wrapper: AssetResponseWrapper = attrs.field(repr=False)
    _mismatch_count: int = 0
    _error_count: int = 0
    _autotag_name: str = "autotag_album_date_mismatch"

    def has_changes(self) -> bool:
        return self._mismatch_count > 0

    def has_errors(self) -> bool:
        return self._error_count > 0

    def get_title(self) -> str:
        return "Album-asset date consistency"

    def get_events(self):
        """Returns events from album date consistency checks (empty, as this check is informational)."""
        from immich_autotag.report.modification_entries_list import (
            ModificationEntriesList,
        )

        return ModificationEntriesList()

    def format(self) -> str:
        parts = [f"mismatches={self._mismatch_count}"]
        if self._error_count:
            parts.append(f"errors={self._error_count}")
        return f"ALBUM_DATE_CONSISTENCY ({', '.join(parts)})"

    @classmethod
    def analyze(
        cls,
        asset_wrapper: AssetResponseWrapper,
        tag_mod_report: ModificationReport,
    ) -> "AlbumDateConsistencyResult":
        result = cls(asset_wrapper=asset_wrapper)
        result._perform_check(tag_mod_report)
        return result

    def _perform_check(self, tag_mod_report: ModificationReport) -> None:
        config = ConfigManager.get_instance().get_config_or_raise()
        if config.album_date_consistency is None:
            raise ValueError("album_date_consistency configuration must not be None")

        if config.album_date_consistency.enabled:
            threshold_days = config.album_date_consistency.threshold_days
        else:
            return

        try:
            asset_date = self._asset_wrapper.get_best_date()
        except Exception as e:
            self._error_count += 1
            log(
                f"[ALBUM_DATE_CONSISTENCY] Could not determine asset date: {e}",
                level=LogLevel.FOCUS,
            )
            return

        albums = (
            self._asset_wrapper.get_context()
            .get_albums_collection()
            .albums_wrappers_for_asset_wrapper(self._asset_wrapper)
        )

        album_date_consistency: AlbumDateConsistencyConfig = (
            config.album_date_consistency
        )
        if album_date_consistency.autotag_album_date_mismatch:
            self._autotag_name = album_date_consistency.autotag_album_date_mismatch

        mismatch_found = False
        for album_wrapper in albums:
            album_name = album_wrapper.get_album_name()
            m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", album_name)
            if not m:
                continue
            year = int(m.group(1))
            month = int(m.group(2)) if m.group(2) else 1
            day = int(m.group(3)) if m.group(3) else 1
            try:
                album_date = datetime(year, month, day, tzinfo=asset_date.tzinfo)
            except Exception as e:
                self._error_count += 1
                log(
                    f"[ALBUM_DATE_CONSISTENCY] Could not parse album date from '{album_name}': {e}",
                    level=LogLevel.FOCUS,
                )
                continue

            diff_days = abs((asset_date - album_date).days)
            if diff_days > threshold_days:
                mismatch_found = True
                self._mismatch_count += 1
                self._asset_wrapper.add_tag_by_name(tag_name=self._autotag_name)
                tag_mod_report.add_modification(
                    kind=ModificationKind.ALBUM_DATE_MISMATCH,
                    asset_wrapper=self._asset_wrapper,
                    album=album_wrapper,
                    old_value=str(album_date.date()),
                    new_value=str(asset_date.date()),
                    extra={
                        "album_name": album_name,
                        "album_date": str(album_date.date()),
                        "asset_date": str(asset_date.date()),
                        "diff_days": diff_days,
                        "autotag": self._autotag_name,
                    },
                )
                log(
                    f"[ALBUM_DATE_CONSISTENCY] Asset {self._asset_wrapper.get_id()} in album '{album_name}' has date mismatch: asset {asset_date.date()} vs album {album_date.date()} (diff {diff_days} days) -- autotagged as '{self._autotag_name}'",
                    level=LogLevel.FOCUS,
                )

        if not mismatch_found and self._asset_wrapper.has_tag(
            tag_name=self._autotag_name
        ):
            self._asset_wrapper.remove_tag_by_name(tag_name=self._autotag_name)
            log(
                f"[ALBUM_DATE_CONSISTENCY] Asset {self._asset_wrapper.get_id()} no longer has a date mismatch. Removed autotag '{self._autotag_name}'.",
                level=LogLevel.FOCUS,
            )


@typechecked
def check_album_date_consistency(
    asset_wrapper: AssetResponseWrapper,
    tag_mod_report: ModificationReport,
) -> AlbumDateConsistencyResult:
    """
    For each album whose name starts with a date (YYYY-MM-DD, YYYY-MM, or YYYY),
    compare the album date to the asset's best date. If the difference is greater than
    threshold_days, add an entry to the modification report.
    """
    return AlbumDateConsistencyResult.analyze(asset_wrapper, tag_mod_report)
