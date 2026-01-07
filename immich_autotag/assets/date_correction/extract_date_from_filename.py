"""
Date patterns in filenames and their origin:

- WhatsApp: IMG-YYYYMMDD-WAxxxx.jpg, WhatsApp Image YYYY-MM-DD at HH.MM.SS.jpg
  Origin: Photos and videos sent/received via WhatsApp.
  Enum: WHATSAPP_FILENAME, WHATSAPP_PATH

- Android/Samsung camera: YYYYMMDD_HHMMSS.jpg
  Origin: Photos taken with the Android/Samsung camera app (default on many mobiles).
  Enum: FILENAME

- iPhone: YYYY-MM-DD_HHMMSS.jpg
  Origin: Photos taken with the iPhone camera app.
  Enum: FILENAME

- Other apps/cameras: May vary, but usually follow similar patterns.

"""

import re
from datetime import datetime
from typing import Optional

from typeguard import typechecked


@typechecked
def extract_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extracts dates from common mobile/camera filenames.
    Supported patterns:
    - Android/Samsung: YYYYMMDD_HHMMSS.jpg
    - iPhone: YYYY-MM-DD_HHMMSS.jpg
    - Others: can be added here
    """
    # Android/Samsung: 20251215_092429.jpg
    m = re.search(r"(\d{8})[_-](\d{6})", filename)
    if m:
        date_str = m.group(1)
        time_str = m.group(2)
        try:
            return datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        except Exception:
            return None
    # iPhone: 2025-12-15_09-24-29.jpg
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})[_-](\d{2})[-_](\d{2})[-_](\d{2})", filename)
    if m:
        try:
            return datetime(
                int(m.group(1)),
                int(m.group(2)),
                int(m.group(3)),
                int(m.group(4)),
                int(m.group(5)),
                int(m.group(6)),
            )
        except Exception:
            return None
    return None
