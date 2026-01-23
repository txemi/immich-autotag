from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_client.models.album_user_response_dto import AlbumUserResponseDto


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumUserWrapper:
    """
    Wrapper for AlbumUserResponseDto to provide a consistent interface for album users.
    """

    user: "AlbumUserResponseDto"

    def __attrs_post_init__(self):
        # Runtime type check for AlbumUserResponseDto
        # noinspection PyUnresolvedReferences,PyTypeHints
        from immich_client.models.album_user_response_dto import AlbumUserResponseDto

        if not isinstance(self.user, AlbumUserResponseDto):
            raise TypeError(f"user must be AlbumUserResponseDto, got {type(self.user)}")

    @property
    @typechecked
    def id(self) -> str:
        return self.user.user.id

    @property
    @typechecked
    def email(self) -> str:
        return self.user.user.email

    @property
    @typechecked
    def name(self) -> str:
        return self.user.user.name

    @typechecked
    def get_uuid(self) -> "UUID":
        from uuid import UUID

        return UUID(self.id)

    def __str__(self) -> str:
        return self.name or self.email or self.id or "<unknown user>"
