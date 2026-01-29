import attrs
from typing import Dict, List

@attrs.define(auto_attribs=True, on_setattr=attrs.setters.validate)
class ResolveEmailsResult:
    resolved: Dict[str, str] = attrs.field(validator=attrs.validators.instance_of(dict))
    unresolved: List[str] = attrs.field(validator=attrs.validators.instance_of(list))

    def __iter__(self):
        # allow unpacking: resolved, unresolved = func(...)
        yield self.resolved
        yield self.unresolved
