import attr
from typing import Any

@attr.define(auto_attribs=True, slots=True)
class Check:
    name: str

    def check(self, args: Any) -> int:
        raise NotImplementedError

    def apply(self, args: Any) -> int:
        raise NotImplementedError
