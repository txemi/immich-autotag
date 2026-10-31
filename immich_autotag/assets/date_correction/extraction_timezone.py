"""The configured extraction timezone, resolved in one place.

A name that is not a timezone (for example "Europe", which is a directory of the tz
database) is logged once and treated as not configured, so a bad setting never aborts
a run. Every reader of `extraction_timezone` goes through here.
"""

from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log

_INVALID_TIMEZONES_LOGGED: set[str] = set()


def parse_timezone(tz_name: Optional[str]) -> Optional[ZoneInfo]:
    """Returns the zone named tz_name, or None if it is empty or not a valid zone."""
    if not tz_name:
        return None
    try:
        return ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        # OSError: a name like "Europe" is a directory of the tz database, not a zone.
        if tz_name not in _INVALID_TIMEZONES_LOGGED:
            _INVALID_TIMEZONES_LOGGED.add(tz_name)
            log(
                f"[DATE CORRECTION] timezone {tz_name!r} is not a valid timezone; "
                "it is ignored (logged once)",
                level=LogLevel.FOCUS,
            )
        return None


def get_extraction_timezone() -> Optional[ZoneInfo]:
    """Returns the configured extraction timezone, or None if unset or invalid."""
    from immich_autotag.config.manager import ConfigManager

    config = ConfigManager.get_instance().get_config()
    duplicate_processing = config.duplicate_processing
    if duplicate_processing is None or duplicate_processing.date_correction is None:
        return None
    return parse_timezone(duplicate_processing.date_correction.extraction_timezone)
