from __future__ import annotations

from typing import TYPE_CHECKING, Optional
import attrs

if TYPE_CHECKING:
    from immich_client.models.user_response_dto import UserResponseDto

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class UserResponseWrapper:
    user: 'UserResponseDto'


    @property
    def id(self) -> str:
        return self.user.id


    @property
    def name(self) -> str:
        return self.user.name


    @property
    def email(self) -> str:
        return self.user.email

    def __str__(self):
        return self.name or self.id or '<unknown user>'
