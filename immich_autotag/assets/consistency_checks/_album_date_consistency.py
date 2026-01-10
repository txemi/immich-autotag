"""
Checks for consistency between asset date and album date (from album name).
If the difference is greater than a threshold (default: 6 months), logs it in the ModificationReport.
"""

from __future__ import annotations

import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from typeguard import typechecked

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.tags.modification_kind import ModificationKind


@typechecked
def check_album_date_consistency(
    asset_wrapper, tag_mod_report, months_threshold: int = 6
):
    """
    For each album whose name starts with a date (YYYY-MM-DD, YYYY-MM, or YYYY),
    compare the album date to the asset's best date. If the difference is greater than
    months_threshold, add an entry to the modification report.
    """
    # Get the best date for the asset (oldest of created_at, file_created_at, exif_created_at)
    try:
        asset_date = asset_wrapper.get_best_date()
    except Exception as e:
        log(
            f"[ALBUM_DATE_CONSISTENCY] Could not determine asset date: {e}",
            level=LogLevel.FOCUS,
        )
        return

    # Get album wrappers for this asset
    albums = asset_wrapper.context.albums_collection.albums_wrappers_for_asset_wrapper(
        asset_wrapper
    )
    from immich_autotag.config.manager import ConfigManager
    config = ConfigManager.get_instance().config
    autotag_name = config.auto_tags.album_date_mismatch
    mismatch_found = False
    for album_wrapper in albums:
        album_name = album_wrapper.album.album_name
        # Match YYYY-MM-DD, YYYY-MM, or YYYY at the start
        m = re.match(r"^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", album_name)
        if not m:
            continue
        year = int(m.group(1))
        month = int(m.group(2)) if m.group(2) else 1
        day = int(m.group(3)) if m.group(3) else 1
        try:
            album_date = datetime(year, month, day, tzinfo=asset_date.tzinfo)
        except Exception as e:
            log(
                f"[ALBUM_DATE_CONSISTENCY] Could not parse album date from '{album_name}': {e}",
                level=LogLevel.FOCUS,
            )
            continue
        diff = relativedelta(asset_date, album_date)
        diff_months = abs(diff.years * 12 + diff.months)
        if diff_months > months_threshold:
            mismatch_found = True
            asset_wrapper.add_tag_by_name(autotag_name)
            tag_mod_report.add_modification(
                kind=ModificationKind.ALBUM_DATE_MISMATCH,
                asset_wrapper=asset_wrapper,
                album=album_wrapper,
                old_value=str(album_date.date()),
                new_value=str(asset_date.date()),
                extra={
                    "album_name": album_name,
                    "album_date": str(album_date.date()),
                    "asset_date": str(asset_date.date()),
                    "diff_months": diff_months,
                    "autotag": autotag_name,
                },
            )
            log(
                f"[ALBUM_DATE_CONSISTENCY] Asset {asset_wrapper.id} in album '{album_name}' has date mismatch: asset {asset_date.date()} vs album {album_date.date()} (diff {diff_months} months) -- autotagged as '{autotag_name}'",
                level=LogLevel.FOCUS,
            )
    # Remove the autotag if no mismatch is found and the tag is present
    if not mismatch_found and asset_wrapper.has_tag(autotag_name):
        asset_wrapper.remove_tag_by_name(autotag_name)
        log(
            f"[ALBUM_DATE_CONSISTENCY] Asset {asset_wrapper.id} no longer has a date mismatch. Removed autotag '{autotag_name}'.",
            level=LogLevel.FOCUS,
        )
