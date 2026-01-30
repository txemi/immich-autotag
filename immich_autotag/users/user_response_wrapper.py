from __future__ import annotations

from typing import TYPE_CHECKING, Union

import attrs
from typeguard import typechecked

from immich_autotag.types.uuid_wrappers import UserUUID

if TYPE_CHECKING:
    from immich_client.models.user_admin_response_dto import UserAdminResponseDto
    from immich_client.models.user_response_dto import UserResponseDto

    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(slots=True, frozen=True)
class UserResponseWrapper:
    @classmethod
    def from_user(cls, user: Union["UserResponseDto", "UserAdminResponseDto"]) -> "UserResponseWrapper":
        return UserResponseWrapper(user=user)

    @staticmethod
    def _validate_user(
        instance: "UserResponseWrapper",
        attribute: Any,
        value: object,
    ) -> None:
        if value is None:
            raise ValueError("user cannot be None")
        from immich_client.models.user_admin_response_dto import (
            UserAdminResponseDto,
        )
        from immich_client.models.user_response_dto import UserResponseDto
        if not isinstance(value, (UserResponseDto, UserAdminResponseDto)):
            raise TypeError(
                f"user must be a UserResponseDto or UserAdminResponseDto, got "
                f"{type(value)}"
            )

    _user: Union["UserResponseDto", "UserAdminResponseDto"] = attrs.field(
        validator=_validate_user,
        init=False
    )

    @typechecked
    def get_name(self) -> str:
        return self._user.name

    @typechecked
    def get_email(self):
        from immich_autotag.types.email_wrapper import EmailWrapper
        return EmailWrapper(self._user.email)

    @classmethod
    @typechecked
    def load_current_user(cls, context: "ImmichContext") -> "UserResponseWrapper":
        """
        Loads and wraps the current user from the context using the UserManager singleton.
        The result is cached in a class variable (assumes immutable user in the session).
        """
        from immich_autotag.users.user_manager import UserManager

        manager = UserManager.get_instance()
        return manager.get_current_user()

    @typechecked
    def get_uuid(self) -> UserUUID:
        return UserUUID.from_string(self._user.id)

    @typechecked
    def __str__(self) -> str:
        return self.get_name() or getattr(self._user, 'id', None) or "<unknown user>"
