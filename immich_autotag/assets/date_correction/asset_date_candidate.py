import attrs
from datetime import datetime
from typing import Optional
from .date_source_kind import DateSourceKind
from immich_client.models.asset_response_dto import AssetResponseDto

@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidate:
    source_kind: DateSourceKind = attrs.field(validator=attrs.validators.instance_of(DateSourceKind))
    date: datetime = attrs.field(validator=attrs.validators.instance_of(datetime))
    file_path: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    asset: Optional[AssetResponseDto] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(AssetResponseDto)))

    def __str__(self):
        return f"AssetDateCandidate(source_kind={self.source_kind}, date={self.date}, file_path={self.file_path}, asset_id={getattr(self.asset, 'id', None)})"
