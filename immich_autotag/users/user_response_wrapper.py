from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

import attrs
from typeguard import typechecked

from immich_autotag.types.email_address import EmailAddress
from immich_autotag.types.uuid_wrappers import UserUUID

if TYPE_CHECKING:
    from immich_client.models.user_admin_response_dto import UserAdminResponseDto
    from immich_client.models.user_response_dto import UserResponseDto


@attrs.define(slots=True, frozen=True)
class UserResponseWrapper:
    _user: Union["UserResponseDto", "UserAdminResponseDto"] = attrs.field()

    @staticmethod
    def _validate_user(user: object) -> None:
        if user is None:
            raise ValueError("user cannot be None")
        from immich_client.models.user_admin_response_dto import UserAdminResponseDto
        from immich_client.models.user_response_dto import UserResponseDto

        if not isinstance(user, (UserResponseDto, UserAdminResponseDto)):
            raise TypeError(
                f"user must be a UserResponseDto or UserAdminResponseDto, got {type(user)}"
            )

    def __attrs_post_init__(self):
        self._validate_user(self._user)

    @classmethod
    def from_user(
        cls, user: Union["UserResponseDto", "UserAdminResponseDto"]
    ) -> "UserResponseWrapper":
        return cls(user)

    @typechecked
    def get_name(self) -> str:
        return self._user.name

    @typechecked
    def get_email(self) -> EmailAddress:
        return EmailAddress.from_string(self._user.email)

    @classmethod
    def load_current_user(cls) -> Optional["UserResponseWrapper"]:
        """
        Loads and wraps the current user from the UserManager singleton.
        The result is cached in a class variable
        (assumes immutable user in the session).
        """
        from immich_autotag.users.user_manager import UserManager

        manager = UserManager.get_instance()
        return manager.get_current_user()

    @typechecked
    def get_uuid(self) -> UserUUID:
        return UserUUID.from_string(self._user.id)

    @typechecked
    def __str__(self) -> str:
        try:
            user_id = self._user.id  # type: ignore[attr-defined]
        except (AttributeError, TypeError):
            user_id = None
        return self.get_name() or user_id or "<unknown user>"
