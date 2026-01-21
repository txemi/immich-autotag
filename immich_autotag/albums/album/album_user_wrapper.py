from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_client.models.album_user_response_dto import AlbumUserResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumUserWrapper:
    """
    Wrapper for AlbumUserResponseDto to provide a consistent interface for album users.
    """

    user: "AlbumUserResponseDto" = attrs.field(
        validator=attrs.validators.instance_of(object)
    )

    @property
    @typechecked
    def id(self) -> str:
        return self.user.id

    @property
    @typechecked
    def email(self) -> str:
        return self.user.email

    @property
    @typechecked
    def name(self) -> str:
        return self.user.name

    def __str__(self) -> str:
        return self.name or self.email or self.id or "<unknown user>"

    @typechecked
    def get_uuid(self) -> "UUID":
        from uuid import UUID

        return UUID(self.id)
