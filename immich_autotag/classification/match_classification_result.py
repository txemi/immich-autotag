from typing import List

import attrs


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class MatchClassificationResult:
    tags_matched: List[str] = attrs.field(validator=attrs.validators.instance_of(list))
    albums_matched: List[str] = attrs.field(
        validator=attrs.validators.instance_of(list)
    )

    def any(self) -> bool:
        return bool(self.tags_matched or self.albums_matched)
