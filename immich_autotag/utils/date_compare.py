from datetime import datetime
from typing import Optional

from typeguard import typechecked


@typechecked
def is_datetime_more_than_days_after(
    dt1: Optional[datetime],
    dt2: Optional[datetime],
    days: float = 1.0,
) -> bool:
    """
    Returns True if dt1 is more than `days` after dt2. Allows floating-point days.
    Args:
        dt1 (datetime): Later date
        dt2 (datetime): Earlier date
        days (float): Threshold in days (can be decimal)
    """
    if dt1 is None or dt2 is None:
        return False
    delta = (dt1 - dt2).total_seconds()
    return delta > days * 86400


@typechecked
def is_datetime_more_than_hours_after(
    dt1: datetime, dt2: datetime, hours: float
) -> bool:
    """
    Return True if dt1 is more than `hours` after dt2.
    Args:
        dt1 (datetime): Later date
        dt2 (datetime): Earlier date
        hours (float): Threshold in hours
    """
    return (dt1 - dt2).total_seconds() > hours * 3600
