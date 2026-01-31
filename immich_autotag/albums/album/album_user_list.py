from __future__ import annotations

from typing import TYPE_CHECKING, Iterator

import attrs
from typeguard import typechecked

from immich_autotag.types.email_address import EmailAddress
from immich_autotag.types.uuid_wrappers import UserUUID

from .album_user_wrapper import AlbumUserWrapper

if TYPE_CHECKING:
    pass


@attrs.define(auto_attribs=True, slots=True)
class AlbumUserList:
    """
    Encapsulates a list of AlbumUserWrapper objects, enforcing type safety and
    providing helper methods.
    """

    _users: list[AlbumUserWrapper] = attrs.field(factory=list)  # type: ignore[type-arg]

    @typechecked
    def append(self, user: "AlbumUserWrapper") -> None:
        # Use isinstance for type safety; AlbumUserWrapper is imported for TYPE_CHECKING
        self._users.append(user)

    @typechecked
    def to_uuid_list(self) -> list[UserUUID]:
        return [u.get_uuid() for u in self._users]

    @typechecked
    def emails(self) -> list[EmailAddress]:
        return [u.get_email() for u in self._users]

    @typechecked
    def names(self) -> list[str]:
        return [u.get_name() for u in self._users]

    @typechecked
    def __getitem__(self, idx: int) -> "AlbumUserWrapper":
        return self._users[idx]

    @typechecked
    def __iter__(self) -> Iterator["AlbumUserWrapper"]:
        return iter(self._users)

    @typechecked
    def __len__(self) -> int:
        return len(self._users)
