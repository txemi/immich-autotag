from __future__ import annotations

import uuid

import attr


@attr.s(frozen=True, slots=True, auto_attribs=True)
class AssetUUID:
    """
    Strongly-typed wrapper for asset UUIDs. Behaves like a UUID but is not equal to a plain UUID.
    Prevents accidental mixing/comparison with other UUID types.
    """

    value: uuid.UUID = attr.ib(converter=uuid.UUID)

    @value.validator
    def _check(self, attribute, value):
        if not isinstance(value, uuid.UUID):
            raise TypeError("value must be a uuid.UUID")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"AssetUUID({str(self.value)})"

    def to_uuid(self) -> uuid.UUID:
        return self.value

    @classmethod
    def from_uuid(cls, value: uuid.UUID) -> "AssetUUID":
        return cls(str(value))

    @classmethod
    def from_str(cls, value: str) -> "AssetUUID":
        return cls(value)
