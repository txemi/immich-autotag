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
    def name(self) -> Optional[str]:
        # Prefer 'name', then 'username', then id
        if hasattr(self.user, 'name') and self.user.name:
            return self.user.name
        if hasattr(self.user, 'username') and self.user.username:
            return self.user.username
        return self.id


    @property
    def email(self) -> Optional[str]:
        return self.user.email if hasattr(self.user, 'email') else None

    def __str__(self):
        return self.name or self.id or '<unknown user>'
