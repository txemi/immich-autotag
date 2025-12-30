import attrs
from datetime import datetime
from typing import Optional

@attrs.define(auto_attribs=True, slots=True)
class AssetDateCandidate:
    label: str = attrs.field(validator=attrs.validators.instance_of(str))
    date: datetime = attrs.field(validator=attrs.validators.instance_of(datetime))
    file_path: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))
    raw_value: Optional[str] = attrs.field(default=None, validator=attrs.validators.optional(attrs.validators.instance_of(str)))

    def __str__(self):
        return f"AssetDateCandidate(label={self.label}, date={self.date}, file_path={self.file_path}, raw_value={self.raw_value})"
