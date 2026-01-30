from __future__ import annotations

from typing import Dict, List, Optional, Union

import attrs
from immich_client.client import AuthenticatedClient as ImmichClient

from immich_autotag.api.immich_proxy.permissions import proxy_search_users
from immich_autotag.api.immich_proxy.users import proxy_get_my_user
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.types.email_address import EmailAddress
from immich_autotag.types.uuid_wrappers import UserUUID
from immich_autotag.users.user_response_wrapper import UserResponseWrapper

# Singleton instance variable (module-level, not attrs-managed)
_USER_MANAGER_INSTANCE: Optional[UserManager] = None


@attrs.define(auto_attribs=True, slots=True)
class UserManager:
    _users: Dict[UserUUID, UserResponseWrapper] = attrs.field(init=False, factory=dict)
    _email_map: Dict[EmailAddress, UserResponseWrapper] = attrs.field(
        init=False, factory=dict
    )
    _context: Optional[ImmichContext] = None
    _loaded: bool = attrs.field(init=False, default=False)
    _current_user: Optional[UserResponseWrapper] = attrs.field(init=False, default=None)

    def __attrs_post_init__(self):
        # Prevent direct instantiation
        global _USER_MANAGER_INSTANCE
        if _USER_MANAGER_INSTANCE is not None:
            raise RuntimeError(
                "Use UserManager.get_instance() instead of direct instantiation."
            )

    @classmethod
    def get_instance(cls) -> "UserManager":
        global _USER_MANAGER_INSTANCE
        if _USER_MANAGER_INSTANCE is None:
            _USER_MANAGER_INSTANCE = cls()
        return _USER_MANAGER_INSTANCE

    def load_all(self, context: ImmichContext) -> None:
        """
        Loads all users from Immich and caches them as UserResponseWrapper instances.
        """
        self._context = context
        client = context.get_client_wrapper().get_client()
        self._load_users(client)
        self._load_current_user(client)
        self._loaded = True

    def _load_users(self, client: ImmichClient) -> None:
        user_dtos = proxy_search_users(client=client) or []
        self._users.clear()
        self._email_map.clear()
        for user_dto in user_dtos:
            wrapper = UserResponseWrapper(user=user_dto)
            self._users[wrapper.get_uuid()] = wrapper
            if wrapper.email:
                email_obj = EmailAddress.from_string(wrapper.email)
                self._email_map[email_obj] = wrapper

    def _load_current_user(self, client: ImmichClient) -> None:
        user_dto = proxy_get_my_user(client=client)
        if user_dto:
            self._current_user = UserResponseWrapper(user=user_dto)
        else:
            self._current_user = None

    def get_by_uuid(self, uuid: UserUUID) -> Optional[UserResponseWrapper]:
        if not self._loaded and self._context:
            self.load_all(self._context)
        return self._users.get(uuid)

    def get_by_email(
        self, email: Union[str, EmailAddress]
    ) -> Optional[UserResponseWrapper]:
        if not self._loaded and self._context:
            self.load_all(self._context)
        email_obj = (
            email
            if isinstance(email, EmailAddress)
            else EmailAddress.from_string(email)
        )
        return self._email_map.get(email_obj)

    def get_current_user(self) -> Optional[UserResponseWrapper]:
        if not self._loaded and self._context:
            self.load_all(self._context)
        return self._current_user

    def all_users(self) -> List[UserResponseWrapper]:
        if not self._loaded and self._context:
            self.load_all(self._context)
        return list(self._users.values())
