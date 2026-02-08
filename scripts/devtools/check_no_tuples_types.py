import attr

@attr.define(auto_attribs=True, slots=True, frozen=True, hash=True, eq=True, order=True)
class NoTuplesFinding:
    file: str
    line: int
    message: str
