from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type, TypeVar

import attrs
from functools import lru_cache

if TYPE_CHECKING:
    from immich_client.models.user_response_dto import UserResponseDto
    from immich_autotag.context.immich_context import ImmichContext



@attrs.define(auto_attribs=True, slots=True, frozen=True)
class UserResponseWrapper:
    user: "UserResponseDto"
    _cached_user_wrapper: Optional["UserResponseWrapper"] = None

    @property
    def id(self) -> str:
        return self.user.id

    @property
    def name(self) -> str:
        return self.user.name

    @property
    def email(self) -> str:
        return self.user.email

    def __str__(self) -> str:
        return self.name or self.id or "<unknown user>"

    @classmethod
    def from_context(cls, context: "ImmichContext") -> "UserResponseWrapper":
        """
        Obtiene el usuario actual usando el cliente/contexto y devuelve un UserResponseWrapper.
        El resultado se cachea en una variable de clase (asume usuario inmutable en la sesión).
        """
        if cls._cached_user_wrapper is not None:
            return cls._cached_user_wrapper  # type: ignore
        from immich_autotag.utils.user_helpers import get_current_user
        user_dto = get_current_user(context)
        cls._cached_user_wrapper = cls(user=user_dto)
        return cls._cached_user_wrapper  # type: ignore

