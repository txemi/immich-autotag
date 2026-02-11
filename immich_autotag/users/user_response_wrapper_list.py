from typing import Iterator

import attrs

from immich_autotag.users.user_response_wrapper import UserResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class UserResponseWrapperList:
    """
    Encapsulates a list of UserResponseWrapper objects, enforcing type safety and providing helper methods.
    """

    _users: list[UserResponseWrapper] = attrs.field(factory=list)

    def append(self, user: UserResponseWrapper) -> None:
        self._users.append(user)

    def deduplicate_by_id(self) -> "UserResponseWrapperList":
        seen = {}
        for user in self._users:
            seen[user._user.id] = user
        return UserResponseWrapperList(list(seen.values()))

    def difference(self, other: "UserResponseWrapperList") -> "UserResponseWrapperList":
        other_ids = {u._user.id for u in other._users}
        diff = [u for u in self._users if u._user.id not in other_ids]
        return UserResponseWrapperList(diff)

    def union(self, other: "UserResponseWrapperList") -> "UserResponseWrapperList":
        combined = self._users + [
            u
            for u in other._users
            if u._user.id not in {x._user.id for x in self._users}
        ]
        return UserResponseWrapperList(combined)

    def to_set(self) -> set[UserResponseWrapper]:
        return set(self._users)

    def to_list(self) -> list[UserResponseWrapper]:
        return list(self._users)

    def __getitem__(self, idx: int) -> UserResponseWrapper:
        return self._users[idx]

    def __iter__(self) -> Iterator[UserResponseWrapper]:
        return iter(self._users)

    def __len__(self) -> int:
        return len(self._users)

    def __repr__(self) -> str:
        return f"UserResponseWrapperList(size={len(self._users)})"
