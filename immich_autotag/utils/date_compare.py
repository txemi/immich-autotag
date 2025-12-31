from datetime import datetime
from typing import Optional

from typeguard import typechecked


@typechecked
def is_datetime_more_than_days_after(
    dt1: Optional[datetime],
    dt2: Optional[datetime],
    days: int = 1,
) -> bool:
    """
    Returns True if dt1 is more than `days` after dt2.
    """
    if dt1 is None or dt2 is None:
        return False
    delta = (dt1 - dt2).total_seconds()
    return delta > days * 86400
