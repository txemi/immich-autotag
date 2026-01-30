import re

import attrs


@attrs.define(auto_attribs=True, frozen=True)
class EmailAddress:
    _value: str = attrs.field()

    def __attrs_post_init__(self):
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", self._value):
            raise ValueError(f"Invalid email address: {self._value}")

    def __str__(self):
        return self._value

    def __repr__(self):
        return f"EmailAddress({self._value!r})"

    @classmethod
    def from_string(cls, value: str) -> "EmailAddress":
        return cls(value)
