from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type, TypeVar

import attrs
from functools import lru_cache

if TYPE_CHECKING:
    from immich_client.models.user_response_dto import UserResponseDto
    from immich_autotag.context.immich_context import ImmichContext


T = TypeVar("T", bound="UserResponseWrapper")

@attrs.define(auto_attribs=True, slots=True, frozen=True)
class UserResponseWrapper:
    user: "UserResponseDto"

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
    def from_context(cls: Type[T], context: "ImmichContext") -> T:
        """
        Obtiene el usuario actual usando el cliente/contexto y devuelve un UserResponseWrapper.
        El resultado se cachea por id del cliente para optimizar (asume usuario inmutable en la sesión).
        """
        cache_key = id(context.client)
        return _get_user_wrapper_cached(cls, context, cache_key)


@lru_cache(maxsize=2)
def _get_user_wrapper_cached(cls: Type[UserResponseWrapper], context: "ImmichContext", cache_key: int) -> UserResponseWrapper:
    from immich_autotag.utils.user_helpers import get_current_user
    user_dto = get_current_user(context)
    return cls(user=user_dto)