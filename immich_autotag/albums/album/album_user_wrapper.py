from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

from immich_autotag.types.email_address import EmailAddress
from immich_autotag.types.uuid_wrappers import UserUUID

if TYPE_CHECKING:
    from immich_client.models.album_user_response_dto import AlbumUserResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumUserWrapper:
    """
    Wrapper for AlbumUserResponseDto to provide a consistent interface for album users.
    """

    _user: "AlbumUserResponseDto" = attrs.field()

    def __attrs_post_init__(self):
        # No runtime validation needed; type is enforced by attrs and static typing
        pass

    @typechecked
    def get_email(self) -> EmailAddress:
        return EmailAddress.from_string(self._user.user.email)

    @typechecked
    def get_name(self) -> str:
        return self._user.user.name

    @typechecked
    def get_uuid(self) -> UserUUID:
        # Try to extract the user id from the wrapped DTO
        return UserUUID.from_string(self._user.user.id)

    def __str__(self) -> str:
        try:
            return self.get_name() or str(self.get_email()) or str(self.get_uuid())
        except Exception:
            return "<unknown user>"
