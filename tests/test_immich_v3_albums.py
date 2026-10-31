"""Album behaviour that changed with Immich v3.

v3 dropped `assets`, `owner` and `ownerId` from the album DTO: the owner is now
in `albumUsers` with role `owner`, and the assets come from POST
/search/metadata filtered by `albumIds`. These tests pin how autotag reads both,
with no server: the HTTP layer is an httpx.MockTransport.
"""

import json
import uuid
from importlib.metadata import version

import httpx
import pytest

immich_client = pytest.importorskip("immich_client")
if int(version("immich-client").split(".")[0]) < 3:
    pytest.skip(
        "the fixtures are Immich v3 DTOs; the client is generated per server",
        allow_module_level=True,
    )
from immich_client.client import AuthenticatedClient  # noqa: E402
from immich_client.models.album_response_dto import AlbumResponseDto  # noqa: E402

from immich_autotag.albums.album.album_dto_state import (  # noqa: E402
    AlbumDtoState,
    AlbumLoadSource,
)
from immich_autotag.api.immich_proxy.albums.get_album_assets import (  # noqa: E402
    proxy_get_album_asset_uuids,
    proxy_is_asset_in_album,
)
from immich_autotag.types.uuid_wrappers import (  # noqa: E402
    AlbumUUID,
    AssetUUID,
    UserUUID,
)

NOW = "2026-10-28T12:00:00.000Z"
ALBUM_ID = str(uuid.uuid4())
OWNER_ID = str(uuid.uuid4())
EDITOR_ID = str(uuid.uuid4())


def _user(user_id: str, name: str) -> dict:
    return {
        "avatarColor": "primary",
        "email": f"{name}@example.org",
        "id": user_id,
        "name": name,
        "profileChangedAt": NOW,
        "profileImagePath": "",
    }


def _album_dict() -> dict:
    return {
        "albumName": "Test album",
        "albumThumbnailAssetId": None,
        "albumUsers": [
            {"role": "owner", "user": _user(OWNER_ID, "owner")},
            {"role": "editor", "user": _user(EDITOR_ID, "editor")},
        ],
        "assetCount": 3,
        "createdAt": NOW,
        "description": "",
        "hasSharedLink": False,
        "id": ALBUM_ID,
        "isActivityEnabled": True,
        "shared": True,
        "updatedAt": NOW,
    }


def _asset(asset_id: str) -> dict:
    return {
        "checksum": "x",
        "createdAt": NOW,
        "duration": None,
        "fileCreatedAt": NOW,
        "fileModifiedAt": NOW,
        "hasMetadata": True,
        "height": 10,
        "id": asset_id,
        "isArchived": False,
        "isEdited": False,
        "isFavorite": False,
        "isOffline": False,
        "isTrashed": False,
        "localDateTime": NOW,
        "originalFileName": "a.jpg",
        "originalPath": "/a.jpg",
        "ownerId": OWNER_ID,
        "thumbhash": None,
        "type": "IMAGE",
        "updatedAt": NOW,
        "visibility": "timeline",
        "width": 10,
    }


def _search_page(asset_ids: list[str], next_page: str | None) -> dict:
    return {
        "albums": {"count": 0, "facets": [], "items": [], "total": 0},
        "assets": {
            "count": len(asset_ids),
            "facets": [],
            "items": [_asset(a) for a in asset_ids],
            "nextCursor": None,
            "nextPage": next_page,
            "total": len(asset_ids),
        },
    }


def _client(handler) -> tuple[AuthenticatedClient, list[dict]]:
    """A client whose requests go to `handler`; also returns the sent bodies."""
    sent: list[dict] = []

    def record(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        sent.append(body)
        return httpx.Response(200, json=handler(body))

    client = AuthenticatedClient(base_url="http://immich.test/api", token="t")
    client.set_httpx_client(
        httpx.Client(
            base_url="http://immich.test/api", transport=httpx.MockTransport(record)
        )
    )
    return client, sent


def test_album_users_leave_the_owner_out():
    state = AlbumDtoState.create(
        dto=AlbumResponseDto.from_dict(_album_dict()),
        load_source=AlbumLoadSource.DETAIL,
    )
    members = [u.get_uuid() for u in state.get_album_users()]
    assert members == [UserUUID(EDITOR_ID)]
    assert state.get_owner_uuid() == UserUUID(OWNER_ID)


def test_detail_without_membership_is_not_full():
    dto = AlbumResponseDto.from_dict(_album_dict())
    state = AlbumDtoState.create(dto=dto, load_source=AlbumLoadSource.DETAIL)
    assert not state.is_full()
    with pytest.raises(RuntimeError):
        state.get_asset_uuids()

    assets = {AssetUUID(uuid.uuid4())}
    full = AlbumDtoState.create(
        dto=dto, load_source=AlbumLoadSource.DETAIL, asset_uuids=assets
    )
    assert full.is_full()
    assert full.get_asset_uuids() == assets
    assert full.get_album_id() == AlbumUUID(ALBUM_ID)

    # A rename (UPDATE) does not change membership: the set survives it.
    full.update(dto=dto, load_source=AlbumLoadSource.UPDATE)
    assert full.is_full()
    assert full.get_asset_uuids() == assets


def test_album_assets_follow_every_page_of_every_visibility():
    timeline = [str(uuid.uuid4()) for _ in range(3)]
    archived = str(uuid.uuid4())

    def handler(body: dict) -> dict:
        if body["visibility"] == "timeline":
            if body["page"] == 1:
                return _search_page(timeline[:2], next_page="2")
            return _search_page(timeline[2:], next_page=None)
        if body["visibility"] == "archive":
            return _search_page([archived], next_page=None)
        return _search_page([], next_page=None)

    client, sent = _client(handler)
    result = proxy_get_album_asset_uuids(album_id=AlbumUUID(ALBUM_ID), client=client)

    # The archived asset counts too: a v2 server leaves it out of a search that
    # sends no visibility.
    assert result == {AssetUUID(a) for a in timeline + [archived]}
    assert [(b["visibility"], b["page"]) for b in sent] == [
        ("timeline", 1),
        ("timeline", 2),
        ("archive", 1),
        ("hidden", 1),
    ]
    assert all(b["albumIds"] == [ALBUM_ID] for b in sent)


def test_is_asset_in_album_finds_an_archived_asset():
    asset_id = str(uuid.uuid4())

    def archived_only(body: dict) -> dict:
        found = [asset_id] if body["visibility"] == "archive" else []
        return _search_page(found, next_page=None)

    client, sent = _client(archived_only)
    assert proxy_is_asset_in_album(
        album_id=AlbumUUID(ALBUM_ID), asset_id=AssetUUID(asset_id), client=client
    )
    assert sent == [
        {"albumIds": [ALBUM_ID], "id": asset_id, "size": 1, "visibility": v}
        for v in ("timeline", "archive")
    ]

    client, sent = _client(lambda body: _search_page([], next_page=None))
    assert not proxy_is_asset_in_album(
        album_id=AlbumUUID(ALBUM_ID), asset_id=AssetUUID(asset_id), client=client
    )
    assert [b["visibility"] for b in sent] == ["timeline", "archive", "hidden"]
