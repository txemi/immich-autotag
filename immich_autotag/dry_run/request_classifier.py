"""
Decides whether an HTTP request to the Immich API reads or writes.

The rule is fail-safe: a request is a read only when it is known to be one.
GET, HEAD and OPTIONS are reads. Immich also searches with POST
(``/search/metadata``, ``/search/smart``, ``/search/random``...): every POST under
``/search/`` is a read too. Anything else (POST, PUT, PATCH, DELETE elsewhere) is
treated as a write, so an endpoint nobody listed here is never sent in a dry run.
"""

from __future__ import annotations

import re
from enum import Enum

_READ_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Immich endpoints that use POST to read. Every path under these prefixes is a
# query: they never change the library.
_POST_READ_PREFIXES = ("/search/",)


class RequestKind(Enum):
    READ = "read"
    WRITE = "write"


class WriteOperation(Enum):
    """The writes the dry run knows how to simulate, by route."""

    CREATE_ALBUM = "create_album"
    UPDATE_ALBUM = "update_album"
    DELETE_ALBUM = "delete_album"
    ADD_ASSETS_TO_ALBUM = "add_assets_to_album"
    REMOVE_ASSETS_FROM_ALBUM = "remove_assets_from_album"
    ADD_USERS_TO_ALBUM = "add_users_to_album"
    UPDATE_ALBUM_USER = "update_album_user"
    REMOVE_USER_FROM_ALBUM = "remove_user_from_album"
    UPDATE_ASSET = "update_asset"
    UPDATE_ASSETS = "update_assets"
    CREATE_TAG = "create_tag"
    DELETE_TAG = "delete_tag"
    TAG_ASSETS = "tag_assets"
    UNTAG_ASSETS = "untag_assets"
    UNKNOWN = "unknown_write"


_SEGMENT = "([^/]+)"

# (method, path pattern, operation). Path patterns are relative to the API base.
_WRITE_ROUTES = [
    ("POST", re.compile(r"^/albums$"), WriteOperation.CREATE_ALBUM),
    ("PATCH", re.compile(rf"^/albums/{_SEGMENT}$"), WriteOperation.UPDATE_ALBUM),
    ("DELETE", re.compile(rf"^/albums/{_SEGMENT}$"), WriteOperation.DELETE_ALBUM),
    (
        "PUT",
        re.compile(rf"^/albums/{_SEGMENT}/assets$"),
        WriteOperation.ADD_ASSETS_TO_ALBUM,
    ),
    (
        "DELETE",
        re.compile(rf"^/albums/{_SEGMENT}/assets$"),
        WriteOperation.REMOVE_ASSETS_FROM_ALBUM,
    ),
    (
        "PUT",
        re.compile(rf"^/albums/{_SEGMENT}/users$"),
        WriteOperation.ADD_USERS_TO_ALBUM,
    ),
    (
        "PUT",
        re.compile(rf"^/albums/{_SEGMENT}/user/{_SEGMENT}$"),
        WriteOperation.UPDATE_ALBUM_USER,
    ),
    (
        "DELETE",
        re.compile(rf"^/albums/{_SEGMENT}/user/{_SEGMENT}$"),
        WriteOperation.REMOVE_USER_FROM_ALBUM,
    ),
    ("PUT", re.compile(rf"^/assets/{_SEGMENT}$"), WriteOperation.UPDATE_ASSET),
    ("PUT", re.compile(r"^/assets$"), WriteOperation.UPDATE_ASSETS),
    ("POST", re.compile(r"^/tags$"), WriteOperation.CREATE_TAG),
    ("DELETE", re.compile(rf"^/tags/{_SEGMENT}$"), WriteOperation.DELETE_TAG),
    ("PUT", re.compile(rf"^/tags/{_SEGMENT}/assets$"), WriteOperation.TAG_ASSETS),
    (
        "DELETE",
        re.compile(rf"^/tags/{_SEGMENT}/assets$"),
        WriteOperation.UNTAG_ASSETS,
    ),
]


class WriteRoute:
    """A write operation plus the ids taken from its path."""

    __slots__ = ("_operation", "_path_ids")

    def __init__(self, operation: WriteOperation, path_ids: list[str]) -> None:
        self._operation = operation
        self._path_ids = path_ids

    def get_operation(self) -> WriteOperation:
        return self._operation

    def get_path_id(self, index: int) -> str:
        return self._path_ids[index]

    def get_path_ids(self) -> list[str]:
        return list(self._path_ids)


def relative_api_path(path: str, base_path: str) -> str:
    """Strips the API base path (``/api`` usually) from a request path."""
    base = base_path.rstrip("/")
    if base and (path == base or path.startswith(base + "/")):
        path = path[len(base) :]
    return path or "/"


def classify_request(method: str, relative_path: str) -> RequestKind:
    """Read or write, with unknown requests counted as writes."""
    upper = method.upper()
    if upper in _READ_METHODS:
        return RequestKind.READ
    if upper == "POST" and any(
        relative_path.startswith(prefix) for prefix in _POST_READ_PREFIXES
    ):
        return RequestKind.READ
    return RequestKind.WRITE


def match_write_route(method: str, relative_path: str) -> WriteRoute:
    """The simulated operation for a write; UNKNOWN when no route matches."""
    upper = method.upper()
    for route_method, pattern, operation in _WRITE_ROUTES:
        if route_method != upper:
            continue
        found = pattern.match(relative_path)
        if found:
            return WriteRoute(operation, list(found.groups()))
    return WriteRoute(WriteOperation.UNKNOWN, [])
