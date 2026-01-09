# extract_whatsapp_date_from_path.py
# Function: extract_whatsapp_date_from_path
import re
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from typeguard import typechecked


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
    # Pattern 1: IMG-YYYYMMDD-WAxxxx or VID-YYYYMMDD-WAxxxx (more robust)
    # Allows hyphens, underscores, spaces, and extensions
    m = re.search(
        r"(?:IMG|VID)[-_]?(\d{4})(\d{2})(\d{2})-WA\d+", str(path), re.IGNORECASE
    )
    if m:
        try:
            from immich_autotag.config.manager import manager

            tz = ZoneInfo(manager.config.features.date_correction.extraction_timezone)
            return datetime(
                int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz
            )
        except Exception:
            return None
    # Pattern 2: WhatsApp Image YYYY-MM-DD at HH.MM.SS
    m = re.search(
        r"WhatsApp (?:Image|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})",
        str(path),
    )
    if m:
        try:
            from immich_autotag.config.manager import manager

            tz = ZoneInfo(manager.config.features.date_correction.extraction_timezone)
            return datetime(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
                int(m.group(4)),
                int(m.group(5)),
                int(m.group(6)),
                tzinfo=tz,
            )
        except Exception:
            return None
    return None
