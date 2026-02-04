"""
Módulo para extracción de UUIDs de enlaces Immich.

Contiene funciones para extraer todos los UUIDs presentes en una URL Immich y distinguir su tipo (álbum, activo, etc.) en futuras versiones.

Por ahora, implementa la lógica original: extraer todos los UUIDs presentes en el string.
"""

import re
from uuid import UUID
from typing import List

def extract_uuids_from_immich_url(url: str) -> List[UUID]:
    """
    Extrae todos los UUIDs presentes en una URL Immich.
    Devuelve una lista de UUIDs encontrados (en orden de aparición).
    """
    uuid_pattern = re.compile(
        r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})"
    )
    return [UUID(match.group(1)) for match in uuid_pattern.finditer(url)]
