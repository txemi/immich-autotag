from __future__ import annotations

import attrs


@attrs.define(auto_attribs=True, slots=True)
class AlbumErrorEntry:
    """Encapsulates a single album-related error event.

    Attributes:
        timestamp: epoch seconds (float) — required
        code: short error code (e.g. "HTTP_400") — required
        message: textual message / representation — optional, defaults to empty string
    """

    timestamp: float = attrs.field(validator=attrs.validators.instance_of(float))
    code: str = attrs.field(validator=attrs.validators.instance_of(str))
    message: str = attrs.field(default="", validator=attrs.validators.instance_of(str))
