from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import attrs
from typeguard import typechecked

if TYPE_CHECKING:
    from immich_client.models.user_response_dto import UserResponseDto

    from immich_autotag.context.immich_context import ImmichContext


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class UserResponseWrapper:
    @staticmethod
    def _validate_user(instance, attribute, value):
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
                f"user must be a UserResponseDto or UserAdminResponseDto, got {type(value)}"
            )

    user: "UserResponseDto" = attrs.field(validator=_validate_user)
    _cached_user_wrapper = None  # Class variable to cache the user

    @property
    @typechecked
    def id(self) -> str:
        return self.user.id

    @property
    @typechecked
    def name(self) -> str:
        return self.user.name

    @property
    @typechecked
    def email(self) -> str:
        return self.user.email

    @typechecked
    def __str__(self) -> str:
        return self.name or self.id or "<unknown user>"

    @classmethod
    @typechecked
    def from_context(cls, context: "ImmichContext") -> "UserResponseWrapper":
        """
        Gets the current user using the client/context and returns a UserResponseWrapper.
        The result is cached in a class variable (assumes immutable user in the session).
        """
        if cls._cached_user_wrapper is not None:
            return cls._cached_user_wrapper  # type: ignore
        from immich_autotag.utils.user_helpers import get_current_user

        user_dto = get_current_user(context)
        cls._cached_user_wrapper = cls(user=user_dto)
        return cls._cached_user_wrapper  # type: ignore
