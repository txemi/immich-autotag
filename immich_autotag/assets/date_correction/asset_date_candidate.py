from datetime import datetime
from typing import Optional

import attrs

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

from .date_source_kind import DateSourceKind


@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidate:



    """
    Representa una fecha candidata ofrecida por un asset (puede ser el asset principal o un duplicado).
    Cada instancia corresponde a una posible fuente de fecha para ese asset, como la fecha de Immich, la fecha extraída del nombre de archivo, del path, EXIF, etc.

    - source_kind: Indica el tipo de fuente de la fecha (ver DateSourceKind).
    - date: La fecha concreta ofrecida por esa fuente.
    - file_path: Ruta o nombre de archivo relevante para la fuente (puede ser None).
    - asset_wrapper: Referencia al asset que ofrece esta fecha (puede ser el principal o un duplicado).

    Ejemplo: Un asset puede tener varias fechas candidatas (Immich, filename, EXIF, etc.), cada una representada por una instancia de esta clase.
    """

    asset_wrapper: AssetResponseWrapper = attrs.field(
        validator=attrs.validators.instance_of(AssetResponseWrapper)
    )
    source_kind: DateSourceKind = attrs.field(
        validator=attrs.validators.instance_of(DateSourceKind)
    )
    date: datetime = attrs.field(validator=attrs.validators.instance_of(datetime))
    file_path: Optional[str] = attrs.field(
        default=None,
        validator=attrs.validators.optional(attrs.validators.instance_of(str)),
    )

    def __str__(self):
        return f"AssetDateCandidate(source_kind={self.source_kind}, date={self.date}, file_path={self.file_path}, asset_id={getattr(self.asset_wrapper, 'id', None)})"

    def get_aware_date(self, user_tz=None):
        """
        Devuelve la fecha garantizando que tiene zona horaria.
        Si la fecha es naive, usa la zona horaria de usuario (user_tz) o la definida en la configuración (DATE_EXTRACTION_TIMEZONE).
        """
        dt = self.date
        if dt.tzinfo is not None:
            return dt
        if user_tz is None:
            from immich_autotag.config.user import DATE_EXTRACTION_TIMEZONE
            from zoneinfo import ZoneInfo
            user_tz = ZoneInfo(DATE_EXTRACTION_TIMEZONE)
        return dt.replace(tzinfo=user_tz)
    def __lt__(self, other):
        if not isinstance(other, AssetDateCandidate):
            return NotImplemented
        return self.get_aware_date() < other.get_aware_date()

    def __eq__(self, other):
        if not isinstance(other, AssetDateCandidate):
            return NotImplemented
        return self.get_aware_date() == other.get_aware_date()