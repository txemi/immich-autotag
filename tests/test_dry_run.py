"""Dry-run mode: nothing is written to Immich, reads keep working, changes are counted.

No real Immich is needed: the "server" is an httpx.MockTransport that answers the
reads with invented data and fails the test if it ever receives a write.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from immich_client.api.albums import (
    add_assets_to_album,
    create_album,
    get_album_info,
    get_all_albums,
    update_album_info,
)
from immich_client.api.assets import update_asset
from immich_client.api.search.search_assets import sync as search_assets
from immich_client.api.tags import create_tag, tag_assets
from immich_client.client import AuthenticatedClient
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.bulk_ids_dto import BulkIdsDto
from immich_client.models.create_album_dto import CreateAlbumDto
from immich_client.models.metadata_search_dto import MetadataSearchDto
from immich_client.models.tag_create_dto import TagCreateDto
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from immich_client.models.update_asset_dto import UpdateAssetDto

from immich_autotag.dry_run import dry_run_mode
from immich_autotag.dry_run.dry_run_session import DryRunSession
from immich_autotag.dry_run.request_classifier import (
    RequestKind,
    classify_request,
    relative_api_path,
)
from immich_autotag.dry_run.simulated_state import is_simulated_id

BASE_URL = "http://immich.example.invalid:2283/api"
NOW = "2024-01-15T10:00:00.000Z"
USER_ID = "11111111-1111-4111-8111-111111111111"
ALBUM_ID = "22222222-2222-4222-8222-222222222222"
ASSET_ID = "33333333-3333-4333-8333-333333333333"
OTHER_ASSET_ID = "44444444-4444-4444-8444-444444444444"
TEMP_ALBUM_NAME = "2024-01-15-autotag-temp-unclassified"

USER = {
    "id": USER_ID,
    "name": "Example Owner",
    "email": "owner@example.invalid",
    "avatarColor": "primary",
    "profileChangedAt": NOW,
    "profileImagePath": "",
}

ALBUM = {
    "id": ALBUM_ID,
    "albumName": "Example album",
    "albumThumbnailAssetId": None,
    "albumUsers": [],
    "assetCount": 0,
    "assets": [],
    "createdAt": NOW,
    "description": "",
    "hasSharedLink": False,
    "isActivityEnabled": True,
    "owner": USER,
    "ownerId": USER_ID,
    "shared": False,
    "updatedAt": NOW,
}


def asset_json(asset_id: str) -> dict:
    return {
        "id": asset_id,
        "checksum": "abc",
        "createdAt": NOW,
        "deviceAssetId": "device-asset",
        "deviceId": "device",
        "duration": "0:00:00.00000",
        "fileCreatedAt": NOW,
        "fileModifiedAt": NOW,
        "hasMetadata": True,
        "height": 100,
        "isArchived": False,
        "isEdited": False,
        "isFavorite": False,
        "isOffline": False,
        "isTrashed": False,
        "localDateTime": NOW,
        "originalFileName": "IMG_0001.jpg",
        "originalPath": "/upload/IMG_0001.jpg",
        "ownerId": USER_ID,
        "thumbhash": None,
        "type": "IMAGE",
        "updatedAt": NOW,
        "visibility": "timeline",
        "width": 100,
        "exifInfo": {"dateTimeOriginal": NOW},
        "tags": [],
    }


def search_json(items: list) -> dict:
    return {
        "albums": {"count": 0, "facets": [], "items": [], "total": 0},
        "assets": {
            "count": len(items),
            "facets": [],
            "items": items,
            "nextPage": None,
            "total": len(items),
        },
    }


class FakeImmich:
    """Answers reads with invented data; records every request it receives."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def writes(self) -> list[str]:
        return [
            f"{r.method} {r.url.path}"
            for r in self.requests
            if classify_request(r.method, relative_api_path(r.url.path, "/api"))
            is RequestKind.WRITE
        ]

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = relative_api_path(request.url.path, "/api")
        method = request.method
        if method == "GET" and path == "/users/me":
            return httpx.Response(200, json=USER)
        if method == "GET" and path == "/albums":
            return httpx.Response(200, json=[ALBUM])
        if method == "GET" and path == f"/albums/{ALBUM_ID}":
            return httpx.Response(200, json=ALBUM)
        if method == "GET" and path.startswith("/assets/"):
            return httpx.Response(200, json=asset_json(path.split("/")[-1]))
        if method == "GET" and path == "/tags":
            return httpx.Response(200, json=[])
        if method == "POST" and path == "/search/metadata":
            return httpx.Response(200, json=search_json([]))
        # A write reaching the server is the failure this mode must prevent.
        return httpx.Response(500, json={"message": f"unexpected {method} {path}"})


@pytest.fixture
def fake_immich() -> FakeImmich:
    return FakeImmich()


@pytest.fixture
def session(tmp_path: Path, fake_immich: FakeImmich):
    DryRunSession.reset()
    started = DryRunSession.start(
        base_url=BASE_URL,
        changes_path=tmp_path / "dry_run_changes.jsonl",
        summary_path=tmp_path / "dry_run_summary.json",
        is_temporary_album=lambda name: "-autotag-temp-unclassified" in name,
        inner=httpx.MockTransport(fake_immich.handler),
    )
    yield started
    DryRunSession.reset()


@pytest.fixture
def client(session: DryRunSession) -> AuthenticatedClient:
    return AuthenticatedClient(
        base_url=BASE_URL,
        token="invented-key",
        prefix="",
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
        httpx_args={"transport": session.get_transport()},
    )


def read_changes(session: DryRunSession) -> list[dict]:
    path = session.get_journal().get_changes_path()
    return [json.loads(line) for line in path.read_text().splitlines()]


# --- read or write --------------------------------------------------------------


@pytest.mark.parametrize(
    "method,path,kind",
    [
        ("GET", "/albums", RequestKind.READ),
        ("HEAD", "/assets/x", RequestKind.READ),
        ("POST", "/search/metadata", RequestKind.READ),
        ("POST", "/search/smart", RequestKind.READ),
        ("POST", "/search/random", RequestKind.READ),
        ("POST", "/albums", RequestKind.WRITE),
        ("PUT", "/albums/x/assets", RequestKind.WRITE),
        ("PATCH", "/albums/x", RequestKind.WRITE),
        ("DELETE", "/tags/x", RequestKind.WRITE),
        ("POST", "/some/endpoint/nobody/listed", RequestKind.WRITE),
        # A proxy could normalise these into POST /albums: never a read.
        ("POST", "/search/%2e%2e/albums", RequestKind.WRITE),
        ("POST", "/search/../albums", RequestKind.WRITE),
    ],
)
def test_classification_counts_unknown_requests_as_writes(method, path, kind):
    assert classify_request(method, path) is kind


def test_relative_api_path_strips_the_api_base():
    assert relative_api_path("/api/search/metadata", "/api") == "/search/metadata"
    assert relative_api_path("/search/metadata", "") == "/search/metadata"


# --- nothing is written, reads keep working --------------------------------------


def test_writes_never_reach_immich(client, fake_immich):
    album = create_album.sync(
        client=client, body=CreateAlbumDto(album_name=TEMP_ALBUM_NAME)
    )
    assert isinstance(album, AlbumResponseDto)
    assert is_simulated_id(str(album.id))
    assert album.owner_id == USER_ID

    added = add_assets_to_album.sync(
        id=album.id, client=client, body=BulkIdsDto(ids=[ASSET_ID, OTHER_ASSET_ID])
    )
    assert added is not None and all(item.success for item in added)

    updated = update_asset.sync(
        id=ASSET_ID,
        client=client,
        body=UpdateAssetDto(date_time_original="2001-02-03T04:05:06+00:00"),
    )
    assert isinstance(updated, AssetResponseDto)

    tag = create_tag.sync(client=client, body=TagCreateDto(name="autotag_output_x"))
    assert isinstance(tag, TagResponseDto)
    tag_assets.sync(id=tag.id, client=client, body=BulkIdsDto(ids=[ASSET_ID]))

    renamed = update_album_info.sync(
        id=ALBUM_ID, client=client, body=UpdateAlbumDto(album_name="Renamed album")
    )
    assert isinstance(renamed, AlbumResponseDto)
    assert renamed.album_name == "Renamed album"

    assert fake_immich.writes() == []


def test_reads_are_sent_and_post_searches_still_work(client, fake_immich):
    albums = get_all_albums.sync(client=client)
    assert albums is not None and [a.album_name for a in albums] == ["Example album"]

    found = search_assets(client=client, body=MetadataSearchDto(page=1, size=10))
    assert found is not None and found.assets.items == []

    sent = [
        f"{r.method} {relative_api_path(r.url.path, '/api')}"
        for r in fake_immich.requests
    ]
    assert sent == ["GET /albums", "POST /search/metadata"]


def test_reads_stay_coherent_with_simulated_writes(client, session, fake_immich):
    album = create_album.sync(
        client=client, body=CreateAlbumDto(album_name=TEMP_ALBUM_NAME)
    )
    assert album is not None
    add_assets_to_album.sync(
        id=album.id, client=client, body=BulkIdsDto(ids=[ASSET_ID])
    )

    # The simulated album is listed and can be read back, without asking Immich.
    names = [a.album_name for a in get_all_albums.sync(client=client) or []]
    assert TEMP_ALBUM_NAME in names
    again = get_album_info.sync(id=album.id, client=client)
    assert isinstance(again, AlbumResponseDto) and again.asset_count == 1

    # The membership check of the pipeline (search by album and asset) sees it.
    body = MetadataSearchDto(album_ids=[album.id], id=ASSET_ID, size=1)
    found = search_assets(client=client, body=body)
    assert found is not None and [str(a.id) for a in found.assets.items] == [ASSET_ID]

    # The date change shows when the asset is read again.
    update_asset.sync(
        id=ASSET_ID,
        client=client,
        body=UpdateAssetDto(date_time_original="2001-02-03T04:05:06+00:00"),
    )
    fetched = httpx.Client(transport=session.get_transport()).get(
        f"{BASE_URL}/assets/{ASSET_ID}"
    )
    assert fetched.json()["exifInfo"]["dateTimeOriginal"].startswith("2001-02-03")

    assert not any(
        is_simulated_id(r.url.path.split("/")[-1]) for r in fake_immich.requests
    )
    assert fake_immich.writes() == []


def test_unknown_write_is_not_sent_and_is_recorded(session, fake_immich):
    http = httpx.Client(transport=session.get_transport())
    response = http.post(f"{BASE_URL}/some/new/endpoint", json={"x": 1})
    assert response.status_code == 501
    assert fake_immich.requests == []
    assert read_changes(session)[0]["operation"] == "unknown_write"


# --- the report of changes --------------------------------------------------------


def test_changes_file_and_summary_counts(client, session):
    album = create_album.sync(
        client=client, body=CreateAlbumDto(album_name=TEMP_ALBUM_NAME)
    )
    assert album is not None
    add_assets_to_album.sync(
        id=album.id, client=client, body=BulkIdsDto(ids=[ASSET_ID, OTHER_ASSET_ID])
    )
    add_assets_to_album.sync(
        id=ALBUM_ID, client=client, body=BulkIdsDto(ids=[ASSET_ID])
    )
    for asset_id in (ASSET_ID, ASSET_ID, OTHER_ASSET_ID):
        update_asset.sync(
            id=asset_id,
            client=client,
            body=UpdateAssetDto(date_time_original="2001-02-03T04:05:06+00:00"),
        )

    changes = read_changes(session)
    assert [c["operation"] for c in changes] == [
        "create_album",
        "add_assets_to_album",
        "add_assets_to_album",
        "update_asset",
        "update_asset",
        "update_asset",
    ]
    assert all(c["sent_to_immich"] is False for c in changes)
    assert changes[1]["target"]["temporary_album"] is True
    assert changes[2]["target"]["temporary_album"] is False
    assert changes[3]["target"]["old_date"] == NOW
    assert changes[4]["target"]["old_date"].startswith("2001-02-03")

    summary = session.finish(completed=True, modification_counts={"CREATE_ALBUM": 1})
    on_disk = json.loads(session.get_journal().get_summary_path().read_text())
    assert on_disk == summary
    assert summary["requests"]["writes_sent_to_immich"] == 0
    assert summary["requests"]["writes_intercepted"] == 6
    assert summary["temporary_albums"] == {
        "albums_created": 1,
        "asset_additions": 2,
        "distinct_assets_added": 2,
        "asset_removals": 0,
    }
    assert summary["asset_dates"] == {"updates": 3, "distinct_assets": 2}
    assert summary["operations"]["add_assets_to_album"] == {"calls": 2, "assets": 3}
    assert summary["simulated_ids"] == [str(album.id)]
    assert summary["modification_report_counts"] == {"CREATE_ALBUM": 1}


# --- switching it on ----------------------------------------------------------------


@pytest.fixture
def clean_mode():
    dry_run_mode.deactivate_dry_run()
    yield
    dry_run_mode.deactivate_dry_run()


def test_env_var_switches_it_on_and_rejects_unknown_values(clean_mode, monkeypatch):
    assert dry_run_mode.is_dry_run_active() is False
    monkeypatch.setenv(dry_run_mode.DRY_RUN_ENV_VAR, "true")
    assert dry_run_mode.is_dry_run_active() is True
    monkeypatch.setenv(dry_run_mode.DRY_RUN_ENV_VAR, "maybe")
    with pytest.raises(ValueError):
        dry_run_mode.is_dry_run_active()


def test_cli_flag_and_misspelt_flag(clean_mode, capsys):
    from immich_autotag.entrypoints.cli_args import apply_cli_args

    apply_cli_args([])
    assert dry_run_mode.is_dry_run_active() is False
    apply_cli_args(["--help"])  # still ignored, as before: the Docker image passes it
    assert dry_run_mode.is_dry_run_active() is False
    with pytest.raises(SystemExit):
        apply_cli_args(["--dryrun"])
    assert dry_run_mode.is_dry_run_active() is False
    apply_cli_args(["--dry-run"])
    assert dry_run_mode.is_dry_run_active() is True


def test_dry_run_output_is_kept_apart_from_real_runs(clean_mode, tmp_path, monkeypatch):
    from immich_autotag.run_output import manager as manager_module

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(manager_module, "_current_instance", None)
    dry_run_mode.activate_dry_run()
    output = manager_module.RunOutputManager.current()
    run_dir = output.get_run_output_dir().path
    assert run_dir.parent == Path("logs_local") / manager_module.DRY_RUN_SUBDIR
    assert output.find_recent_run_dirs() == []
    assert output.get_previous_run_output_dir() is None
    monkeypatch.setattr(manager_module, "_current_instance", None)


def test_client_wrapper_installs_the_dry_run_transport(
    clean_mode, session, fake_immich, monkeypatch
):
    from immich_autotag.config import host_config
    from immich_autotag.context import immich_client_wrapper as wrapper_module

    config = SimpleNamespace(server=SimpleNamespace(api_key="invented-key"))
    monkeypatch.setattr(
        wrapper_module.ConfigManager,
        "get_instance",
        staticmethod(lambda: SimpleNamespace(get_config=lambda: config)),
    )
    monkeypatch.setattr(host_config, "get_immich_base_url", lambda: BASE_URL)
    monkeypatch.setattr(wrapper_module, "_singleton", None)
    dry_run_mode.activate_dry_run()

    client = wrapper_module.ImmichClientWrapper().get_client()
    album = create_album.sync(client=client, body=CreateAlbumDto(album_name="Example"))
    assert album is not None and is_simulated_id(str(album.id))
    assert fake_immich.writes() == []
    monkeypatch.setattr(wrapper_module, "_singleton", None)


def test_client_built_before_the_switch_is_refused(clean_mode, monkeypatch):
    from immich_autotag.context import immich_client_wrapper as wrapper_module

    monkeypatch.setattr(wrapper_module, "_singleton", None)
    wrapper = wrapper_module.ImmichClientWrapper()
    monkeypatch.setattr(
        wrapper, "_build_client", lambda: MagicMock(spec=AuthenticatedClient)
    )
    wrapper.get_client()
    dry_run_mode.activate_dry_run()
    with pytest.raises(RuntimeError):
        wrapper.get_client()
    monkeypatch.setattr(wrapper_module, "_singleton", None)


def test_encoded_search_path_is_not_sent(session, fake_immich):
    with httpx.Client(transport=session.get_transport()) as raw_client:
        raw_client.post(BASE_URL + "/search/%2e%2e/albums", json={})
    assert fake_immich.requests == []


def test_run_main_reads_the_flag_before_the_pipeline(clean_mode, monkeypatch):
    import sys

    from immich_autotag import main_entrypoint as top_level

    seen = {}

    def fake_run_main():
        seen["dry_run"] = dry_run_mode.is_dry_run_active()

    monkeypatch.setattr(sys, "argv", ["immich_autotag", "--dry-run"])
    monkeypatch.setitem(
        sys.modules,
        "immich_autotag.entrypoints.main_entrypoint",
        SimpleNamespace(run_main=fake_run_main),
    )
    top_level.run_main()
    assert seen == {"dry_run": True}


def test_normal_run_does_not_install_the_dry_run_transport(clean_mode, monkeypatch):
    from immich_autotag.config import host_config
    from immich_autotag.context import immich_client_wrapper as wrapper_module

    config = SimpleNamespace(server=SimpleNamespace(api_key="invented-key"))
    monkeypatch.setattr(
        wrapper_module.ConfigManager,
        "get_instance",
        staticmethod(lambda: SimpleNamespace(get_config=lambda: config)),
    )
    monkeypatch.setattr(host_config, "get_immich_base_url", lambda: BASE_URL)
    built = {}
    from immich_autotag.types import client_types

    monkeypatch.setattr(
        client_types, "ImmichClient", lambda **kwargs: built.update(kwargs) or object()
    )
    monkeypatch.setattr(wrapper_module, "_singleton", None)

    wrapper_module.ImmichClientWrapper().get_client()
    assert "transport" not in built["httpx_args"]
    monkeypatch.setattr(wrapper_module, "_singleton", None)
