import uuid

import attrs


def _uuid_converter(val):
    if isinstance(val, uuid.UUID):
        return val
    if isinstance(val, str):
        return uuid.UUID(val)
    if isinstance(val, bytes):
        return uuid.UUID(bytes=val)
    raise TypeError("Value must be uuid.UUID, str, or bytes")


def _uuid_validator(instance, attribute, value):
    if not isinstance(value, uuid.UUID):
        raise TypeError(f"{attribute.name} must be a uuid.UUID, got {type(value)}")


@attrs.define(frozen=True, auto_attribs=True)
class BaseUUIDWrapper:
    value: uuid.UUID = attrs.field(converter=_uuid_converter, validator=_uuid_validator)

    @classmethod
    def from_string(cls, s: str):
        return cls(uuid.UUID(s))

    @classmethod
    def from_bytes(cls, b: bytes):
        return cls(uuid.UUID(bytes=b))

    @classmethod
    def random(cls):
        return cls(uuid.uuid4())

    @classmethod
    def from_uuid(cls, value: uuid.UUID):
        return cls(value)

    def to_uuid(self) -> uuid.UUID:
        return self.value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class AssetUUID(BaseUUIDWrapper):
    pass


class TagUUID(BaseUUIDWrapper):
    pass


class AlbumUUID(BaseUUIDWrapper):
    pass


# New: UserUUID for user identifiers
class UserUUID(BaseUUIDWrapper):
    pass
