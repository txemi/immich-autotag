from __future__ import annotations

from typing import TYPE_CHECKING, Union

import attrs
from typeguard import typechecked

from immich_autotag.types.uuid_wrappers import UserUUID

if TYPE_CHECKING:
    from immich_client.models.user_admin_response_dto import UserAdminResponseDto
    from immich_client.models.user_response_dto import UserResponseDto

    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class UserResponseWrapper:

    @staticmethod
    def _validate_user(
        instance: "UserResponseWrapper",
        attribute: attrs.Attribute["UserResponseDto"],
        value: object,
    ) -> None:
        if value is None:
            raise ValueError("user cannot be None")
        try:
            from immich_client.models.user_admin_response_dto import (
                UserAdminResponseDto,
            )
            from immich_client.models.user_response_dto import UserResponseDto
        except ImportError:
            raise TypeError(
                "UserResponseDto/UserAdminResponseDto type cannot be imported for validation"
            )
        if not isinstance(value, (UserResponseDto, UserAdminResponseDto)):
            raise TypeError(
                f"user must be a UserResponseDto or UserAdminResponseDto, got "
                f"{type(value)}"
            )

    user: Union["UserResponseDto", "UserAdminResponseDto"] = attrs.field(
        validator=_validate_user
    )
    _cached_user_wrapper = None  # Class variable to cache the user

    @property
    @typechecked
    def name(self) -> str:
        return self.user.name

    @property
    @typechecked
    def email(self) -> str:
        return self.user.email

    @classmethod
    @typechecked
    def load_current_user(cls, context: "ImmichContext") -> "UserResponseWrapper":
        """
        Loads and wraps the current user from the context using the UserManager singleton.
        The result is cached in a class variable (assumes immutable user in the session).
        """
        if cls._cached_user_wrapper is not None:
            return cls._cached_user_wrapper  # type: ignore
        from immich_autotag.users.user_manager import UserManager

        manager = UserManager.get_instance()
        manager.load_all(context)
        user_wrapper = manager.get_current_user()
        cls._cached_user_wrapper = user_wrapper
        return cls._cached_user_wrapper  # type: ignore

    @typechecked
    def get_uuid(self) -> UserUUID:
        return UserUUID.from_string(self.user.id)

    @typechecked
    def __str__(self) -> str:
        return self.name or self.id or "<unknown user>"
