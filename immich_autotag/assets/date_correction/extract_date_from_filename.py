"""
Patrones de fechas en nombres de fichero y su origen:

- WhatsApp: IMG-YYYYMMDD-WAxxxx.jpg, WhatsApp Image YYYY-MM-DD at HH.MM.SS.jpg
  Origen: Fotos y vídeos enviados/recibidos por WhatsApp.
  Enum: WHATSAPP_FILENAME, WHATSAPP_PATH

- Android/Samsung cámara: YYYYMMDD_HHMMSS.jpg
  Origen: Fotos tomadas con la app de cámara de Android/Samsung (por defecto en muchos móviles).
  Enum: FILENAME

- iPhone: YYYY-MM-DD_HHMMSS.jpg
  Origen: Fotos tomadas con la app de cámara de iPhone.
  Enum: FILENAME

- Otras apps/cámaras: Pueden variar, pero suelen seguir patrones similares.

"""

import re
from datetime import datetime
from typing import Optional

from typeguard import typechecked


@typechecked
def extract_date_from_filename(filename: str) -> Optional[datetime]:
    """
    Extrae fechas de nombres de fichero comunes en móviles/cámaras.
    Patrones soportados:
    - Android/Samsung: YYYYMMDD_HHMMSS.jpg
    - iPhone: YYYY-MM-DD_HHMMSS.jpg
    - Otros: se pueden añadir aquí
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
