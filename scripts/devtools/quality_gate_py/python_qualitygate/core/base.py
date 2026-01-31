
from typing import Any

class Check:
    name: str = ''  # Should be overridden as a class variable in subclasses

    def check(self, args: Any) -> int:
        raise NotImplementedError

    def apply(self, args: Any) -> int:
        raise NotImplementedError
