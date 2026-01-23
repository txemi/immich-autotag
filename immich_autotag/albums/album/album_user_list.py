from __future__ import annotations

from typing import TYPE_CHECKING, Iterator
from uuid import UUID

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from .album_user_wrapper import AlbumUserWrapper


@attrs.define(auto_attribs=True, slots=True)
class AlbumUserList:
    """
    Encapsulates a list of AlbumUserWrapper objects, enforcing type safety and
    providing helper methods.
    """

    _users: list["AlbumUserWrapper"] = attrs.field(factory=list)

    @typechecked
    def append(self, user: "AlbumUserWrapper") -> None:
        # Use isinstance for type safety; AlbumUserWrapper is imported for TYPE_CHECKING
        self._users.append(user)

    @typechecked
    def to_id_list(self) -> list[str]:
        return [u.id for u in self._users]

    @typechecked
    def to_uuid_list(self) -> list["UUID"]:
        return [u.get_uuid() for u in self._users]

    @typechecked
    def emails(self) -> list[str]:
        return [u.email for u in self._users]

    @typechecked
    def names(self) -> list[str]:
        return [u.name for u in self._users]

    @typechecked
    def __getitem__(self, idx: int) -> "AlbumUserWrapper":
        return self._users[idx]

    @typechecked
    def __iter__(self) -> Iterator["AlbumUserWrapper"]:
        return iter(self._users)

    @typechecked
    def __len__(self) -> int:
        return len(self._users)
