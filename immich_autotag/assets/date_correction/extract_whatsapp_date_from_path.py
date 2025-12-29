# extract_whatsapp_date_from_path.py
# Función: extract_whatsapp_date_from_path
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
    # Historial de casos reales que han motivado cambios en la función:
    - 'VID-20251229-WA0004.mp4'  # Caso real: no detectado inicialmente, añadido soporte robusto para este patrón
    ---
    """
    # Pattern 1: IMG-YYYYMMDD-WAxxxx or VID-YYYYMMDD-WAxxxx (más robusto)
    # Permite guiones, subrayados, espacios, y extensiones
    m = re.search(r"(?:IMG|VID)[-_]?(\d{4})(\d{2})(\d{2})-WA\d+", str(path), re.IGNORECASE)
    if m:
        try:
            tz = ZoneInfo(DATE_EXTRACTION_TIMEZONE)
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=tz)
        except Exception:
            return None
    # Pattern 2: WhatsApp Image YYYY-MM-DD at HH.MM.SS
    m = re.search(r"WhatsApp (?:Image|Video) (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})", str(path))
    if m:
        try:
            tz = ZoneInfo(DATE_EXTRACTION_TIMEZONE)
            return datetime(
                int(m.group(1)), int(m.group(2)), int(m.group(3)),
                int(m.group(4)), int(m.group(5)), int(m.group(6)),
                tzinfo=tz
            )
        except Exception:
            return None
    return None
