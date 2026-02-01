# extract_whatsapp_date_from_path.py
# Function: extract_whatsapp_date_from_path
import re
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from typeguard import typechecked

from immich_autotag.config.models import UserConfig


def _get_extraction_timezone() -> Optional[ZoneInfo]:
    """Get configured timezone for date extraction, or None if not configured."""
    try:
        from immich_autotag.config.manager import ConfigManager

        config: UserConfig = ConfigManager.get_instance().get_config_or_raise()
        if config.duplicate_processing is None:
            return None
        return ZoneInfo(
            config.duplicate_processing.date_correction.extraction_timezone
        )
    except Exception:
        return None


def _extract_img_vid_pattern(path: str, tz: ZoneInfo) -> Optional[datetime]:
    """
    Extract date from IMG-YYYYMMDD-WAxxxx or VID-YYYYMMDD-WAxxxx pattern.
    Example: 'VID-20251229-WA0004.mp4' -> datetime(2025, 12, 29, tzinfo=tz)
    """
    m = re.search(
        r"(?:IMG|VID)[-_]?(\d{4})(\d{2})(\d{2})-WA\d+", str(path), re.IGNORECASE
    )
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz
        )
    except (ValueError, OverflowError):
        # Invalid date values (e.g., month=13, day=32)
        return None


def _extract_full_timestamp_pattern(path: str, tz: ZoneInfo) -> Optional[datetime]:
    """
    Extract date from 'WhatsApp Image YYYY-MM-DD at HH.MM.SS' pattern.
    Example: 'WhatsApp Image 2025-12-29 at 14.30.45.jpeg' -> datetime(2025, 12, 29, 14, 30, 45, tzinfo=tz)
    """
    m = re.search(
        r"WhatsApp (?:Image|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})",
        str(path),
    )
    if not m:
        return None
    try:
        return datetime(
            int(m.group(1)),
            int(m.group(2)),
            int(m.group(3)),
            int(m.group(4)),
            int(m.group(5)),
            int(m.group(6)),
            tzinfo=tz,
        )
    except (ValueError, OverflowError):
        # Invalid date/time values
        return None


@typechecked
def extract_whatsapp_date_from_path(path: str) -> Optional[datetime]:
    """
    Try to extract a date from WhatsApp-style filenames or paths.
    Supports patterns like:
      - IMG-YYYYMMDD-WAxxxx.jpg
      - VID-YYYYMMDD-WAxxxx.mp4
      - WhatsApp Image YYYY-MM-DD at HH.MM.SS.jpeg
      - WhatsApp Video YYYY-MM-DD at HH.MM.SS.mp4
    Returns a datetime if found, else None.

    ---
    # History of real cases that motivated changes to the function:
    - 'VID-20251229-WA0004.mp4'  # Real case: not initially detected, robust support added for this pattern
    ---
    """
    tz = _get_extraction_timezone()
    if tz is None:
        return None

    # Try pattern 1: IMG-YYYYMMDD-WAxxxx or VID-YYYYMMDD-WAxxxx
    result = _extract_img_vid_pattern(path, tz)
    if result is not None:
        return result

    # Try pattern 2: WhatsApp Image YYYY-MM-DD at HH.MM.SS
    result = _extract_full_timestamp_pattern(path, tz)
    if result is not None:
        return result

    return None
