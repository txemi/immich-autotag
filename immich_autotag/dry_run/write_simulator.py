"""
Answers the writes of a dry run without sending them.

Every write is recorded in the journal and answered with what Immich would
answer, so the pipeline goes on as in a real pass. When the answer needs data
from the server (the album being renamed, the asset whose date changes), it is
read with a GET; when it needs something that would only exist after the write
(the id of a new album or tag), a simulated id is used and recorded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from immich_autotag.dry_run.change_journal import DryRunJournal
from immich_autotag.dry_run.http_helpers import (
    empty_response,
    error_response,
    json_response,
    read_json_body,
    string_list,
)
from immich_autotag.dry_run.read_overlay import ReadOverlay
from immich_autotag.dry_run.request_classifier import (
    WriteOperation,
    WriteRoute,
    match_write_route,
)
from immich_autotag.dry_run.simulated_state import SimulatedState, is_simulated_id
from immich_autotag.dry_run.upstream_reader import UpstreamReader

_ALBUM_EDITABLE_FIELDS = frozenset(
    {"albumName", "description", "albumThumbnailAssetId", "isActivityEnabled", "order"}
)

# Album fields that describe the album a template was copied from, not a new one.
_ALBUM_FIELDS_NOT_COPIED = frozenset(
    {"startDate", "endDate", "lastModifiedAssetTimestamp", "contributorCounts"}
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bulk_result(asset_ids: list[str], duplicates: list[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for asset_id in asset_ids:
        if asset_id in duplicates:
            result.append({"id": asset_id, "success": False, "error": "duplicate"})
        else:
            result.append({"id": asset_id, "success": True})
    return result


class _Outcome:
    __slots__ = ("response", "target", "asset_ids", "simulated_ids")

    def __init__(
        self,
        *,
        response: httpx.Response,
        target: dict[str, Any],
        asset_ids: list[str] | None = None,
        simulated_ids: list[str] | None = None,
    ) -> None:
        self.response = response
        self.target = target
        self.asset_ids = asset_ids or []
        self.simulated_ids = simulated_ids or []


class WriteSimulator:
    def __init__(
        self,
        *,
        state: SimulatedState,
        journal: DryRunJournal,
        upstream: UpstreamReader,
        overlay: ReadOverlay,
    ) -> None:
        self._state = state
        self._journal = journal
        self._upstream = upstream
        self._overlay = overlay

    def _current_album(
        self, request: httpx.Request, album_id: str
    ) -> dict[str, Any] | None:
        """The album as the simulation sees it now (simulated or real + overrides)."""
        if self._state.is_deleted(album_id):
            return None
        if is_simulated_id(album_id):
            return self._state.get_simulated_album(album_id)
        album = self._upstream.get_json(
            request, f"/albums/{album_id}", "withoutAssets=true"
        )
        if not isinstance(album, dict):
            return None
        self._state.learn_album(album)
        return self._state.apply_album_overrides(album)

    # --- helpers ------------------------------------------------------------

    def _album_target(
        self, album_id: str, request: httpx.Request | None = None
    ) -> dict[str, Any]:
        name = self._state.get_album_name(album_id)
        if name is None and request is not None and not is_simulated_id(album_id):
            # Not seen yet: one cached GET gives its name, so that additions to
            # temporary albums are always counted as such.
            self._current_album(request, album_id)
            name = self._state.get_album_name(album_id)
        return {
            "album_id": album_id,
            "album_name": name,
            "album_simulated": is_simulated_id(album_id),
            "temporary_album": self._journal.is_temporary_album_name(name),
        }

    def _current_user(self, request: httpx.Request) -> dict[str, Any]:
        user = self._upstream.get_json(request, "/users/me")
        if isinstance(user, dict):
            return user
        now = _now_iso()
        return {
            "id": "00000000-0000-4000-8000-000000000000",
            "name": "dry-run",
            "email": "dry-run@example.invalid",
            "avatarColor": "primary",
            "profileChangedAt": now,
            "profileImagePath": "",
        }

    def _user(self, request: httpx.Request, user_id: str) -> dict[str, Any]:
        user = self._upstream.get_json(request, f"/users/{user_id}")
        if isinstance(user, dict):
            return user
        return {"id": user_id}

    # --- albums -------------------------------------------------------------

    def _create_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        name = str(body.get("albumName", ""))
        owner = self._current_user(request)
        album = {
            k: v
            for k, v in (self._state.get_album_template() or {}).items()
            if k not in _ALBUM_FIELDS_NOT_COPIED
        }
        now = _now_iso()
        album_id = self._state.new_simulated_id()
        album.update(
            {
                "id": album_id,
                "albumName": name,
                "description": str(body.get("description", "")),
                "albumThumbnailAssetId": None,
                "albumUsers": [],
                "assetCount": 0,
                "assets": [],
                "createdAt": now,
                "updatedAt": now,
                "hasSharedLink": False,
                "isActivityEnabled": True,
                "owner": owner,
                "ownerId": owner.get("id"),
                "shared": False,
            }
        )
        self._state.add_simulated_album(album)
        asset_ids = string_list(body.get("assetIds"))
        self._state.add_members(album_id, asset_ids)
        response_album = self._state.get_simulated_album(album_id) or album
        return _Outcome(
            response=json_response(201, response_album),
            target=self._album_target(album_id, request),
            asset_ids=asset_ids,
            simulated_ids=[album_id],
        )

    def _update_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        if self._current_album(request, album_id) is None:
            return _Outcome(
                response=error_response(404, "Album not found"),
                target=self._album_target(album_id, request),
            )
        previous_name = self._state.get_album_name(album_id)
        fields = {k: v for k, v in body.items() if k in _ALBUM_EDITABLE_FIELDS}
        self._state.override_album(album_id, fields)
        target = self._album_target(album_id, request)
        target["previous_album_name"] = previous_name
        target["fields"] = sorted(fields)
        album = self._current_album(request, album_id) or {}
        return _Outcome(response=json_response(200, album), target=target)

    def _delete_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        target = self._album_target(album_id, request)
        self._state.mark_deleted(album_id)
        return _Outcome(response=empty_response(204), target=target)

    def _add_assets_to_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        asset_ids = string_list(body.get("ids"))
        duplicates = self._state.add_members(album_id, asset_ids)
        return _Outcome(
            response=json_response(200, _bulk_result(asset_ids, duplicates)),
            target=self._album_target(album_id, request),
            asset_ids=asset_ids,
        )

    def _remove_assets_from_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        asset_ids = string_list(body.get("ids"))
        self._state.remove_members(album_id, asset_ids)
        return _Outcome(
            response=json_response(200, _bulk_result(asset_ids, [])),
            target=self._album_target(album_id, request),
            asset_ids=asset_ids,
        )

    def _add_users_to_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        album = self._current_album(request, album_id)
        target = self._album_target(album_id, request)
        new_users = [u for u in body.get("albumUsers", []) if isinstance(u, dict)]
        target["users"] = [
            {"user_id": u.get("userId"), "role": u.get("role")} for u in new_users
        ]
        if album is None:
            return _Outcome(
                response=error_response(404, "Album not found"), target=target
            )
        album_users = list(album.get("albumUsers") or [])
        for new_user in new_users:
            album_users.append(
                {
                    "user": self._user(request, str(new_user.get("userId"))),
                    "role": new_user.get("role", "editor"),
                }
            )
        self._state.override_album(album_id, {"albumUsers": album_users})
        album["albumUsers"] = album_users
        album["shared"] = True
        return _Outcome(response=json_response(200, album), target=target)

    def _change_album_user(
        self,
        request: httpx.Request,
        album_id: str,
        user_id: str,
        role: Any,
    ) -> None:
        """Updates the simulated users of an album: a role, or removal if None."""
        album = self._current_album(request, album_id)
        if album is None:
            return
        album_users = []
        for entry in album.get("albumUsers") or []:
            user = entry.get("user") if isinstance(entry, dict) else None
            if isinstance(user, dict) and user.get("id") == user_id:
                if role is None:
                    continue
                entry = dict(entry)
                entry["role"] = role
            album_users.append(entry)
        self._state.override_album(album_id, {"albumUsers": album_users})

    def _update_album_user(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        user_id = route.get_path_id(1)
        role = body.get("role")
        self._change_album_user(request, album_id, user_id, role)
        target = self._album_target(album_id, request)
        target["user_id"] = user_id
        target["role"] = role
        return _Outcome(response=empty_response(204), target=target)

    def _remove_user_from_album(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        album_id = route.get_path_id(0)
        user_id = route.get_path_id(1)
        self._change_album_user(request, album_id, user_id, None)
        target = self._album_target(album_id, request)
        target["user_id"] = user_id
        return _Outcome(response=empty_response(204), target=target)

    # --- assets -------------------------------------------------------------

    def _update_asset(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        asset_id = route.get_path_id(0)
        before = self._overlay.fetch_asset(request, asset_id)
        target: dict[str, Any] = {
            "asset_id": asset_id,
            "fields": sorted(body),
            "changes_date": "dateTimeOriginal" in body,
        }
        if before is None:
            return _Outcome(
                response=error_response(404, "Asset not found"),
                target=target,
                asset_ids=[asset_id],
            )
        exif = before.get("exifInfo")
        if "dateTimeOriginal" in body:
            target["old_date"] = (
                exif.get("dateTimeOriginal") if isinstance(exif, dict) else None
            )
            target["new_date"] = body["dateTimeOriginal"]
        self._state.override_asset(asset_id, body)
        after = self._overlay.fetch_asset(request, asset_id) or before
        return _Outcome(
            response=json_response(200, after),
            target=target,
            asset_ids=[asset_id],
        )

    def _update_assets(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        asset_ids = string_list(body.get("ids"))
        fields = {k: v for k, v in body.items() if k != "ids"}
        for asset_id in asset_ids:
            self._state.override_asset(asset_id, fields)
        target = {
            "fields": sorted(fields),
            "changes_date": "dateTimeOriginal" in fields,
        }
        return _Outcome(
            response=empty_response(204), target=target, asset_ids=asset_ids
        )

    # --- tags ---------------------------------------------------------------

    def _tag_target(self, tag_id: str) -> dict[str, Any]:
        return {"tag_id": tag_id, "tag_simulated": is_simulated_id(tag_id)}

    def _create_tag(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        name = str(body.get("name", ""))
        tag = {
            k: v
            for k, v in (self._state.get_tag_template() or {}).items()
            if k not in {"parentId", "color"}
        }
        now = _now_iso()
        tag_id = self._state.new_simulated_id()
        tag.update(
            {
                "id": tag_id,
                "name": name,
                "value": name,
                "createdAt": now,
                "updatedAt": now,
            }
        )
        for optional in ("color", "parentId"):
            if body.get(optional) is not None:
                tag[optional] = body[optional]
        self._state.add_simulated_tag(tag)
        target = self._tag_target(tag_id)
        target["tag_name"] = name
        return _Outcome(
            response=json_response(201, tag), target=target, simulated_ids=[tag_id]
        )

    def _delete_tag(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        tag_id = route.get_path_id(0)
        self._state.mark_deleted(tag_id)
        return _Outcome(response=empty_response(204), target=self._tag_target(tag_id))

    def _tag_assets(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        tag_id = route.get_path_id(0)
        self._state.mark_as_tag(tag_id)
        asset_ids = string_list(body.get("ids"))
        duplicates = self._state.add_members(tag_id, asset_ids)
        return _Outcome(
            response=json_response(200, _bulk_result(asset_ids, duplicates)),
            target=self._tag_target(tag_id),
            asset_ids=asset_ids,
        )

    def _untag_assets(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        tag_id = route.get_path_id(0)
        self._state.mark_as_tag(tag_id)
        asset_ids = string_list(body.get("ids"))
        self._state.remove_members(tag_id, asset_ids)
        return _Outcome(
            response=json_response(200, _bulk_result(asset_ids, [])),
            target=self._tag_target(tag_id),
            asset_ids=asset_ids,
        )

    # --- anything else ------------------------------------------------------

    def _unknown(
        self, request: httpx.Request, route: WriteRoute, body: dict[str, Any]
    ) -> "_Outcome":
        """A write with no simulation: not sent, and answered with an error."""
        return _Outcome(
            response=error_response(
                501,
                "Dry run: this write has no simulation and was NOT sent to Immich.",
            ),
            target={"unknown": True},
        )

    def simulate(self, request: httpx.Request, relative_path: str) -> httpx.Response:
        route = match_write_route(request.method, relative_path)
        body = read_json_body(request)
        operation = route.get_operation()
        handlers = {
            WriteOperation.CREATE_ALBUM: self._create_album,
            WriteOperation.UPDATE_ALBUM: self._update_album,
            WriteOperation.DELETE_ALBUM: self._delete_album,
            WriteOperation.ADD_ASSETS_TO_ALBUM: self._add_assets_to_album,
            WriteOperation.REMOVE_ASSETS_FROM_ALBUM: self._remove_assets_from_album,
            WriteOperation.ADD_USERS_TO_ALBUM: self._add_users_to_album,
            WriteOperation.UPDATE_ALBUM_USER: self._update_album_user,
            WriteOperation.REMOVE_USER_FROM_ALBUM: self._remove_user_from_album,
            WriteOperation.UPDATE_ASSET: self._update_asset,
            WriteOperation.UPDATE_ASSETS: self._update_assets,
            WriteOperation.CREATE_TAG: self._create_tag,
            WriteOperation.DELETE_TAG: self._delete_tag,
            WriteOperation.TAG_ASSETS: self._tag_assets,
            WriteOperation.UNTAG_ASSETS: self._untag_assets,
        }
        handler = handlers.get(operation, self._unknown)
        outcome = handler(request, route, body if isinstance(body, dict) else {})
        self._journal.record_write(
            operation=operation,
            method=request.method.upper(),
            path=relative_path,
            target=outcome.target,
            asset_ids=outcome.asset_ids,
            body=body,
            simulated_status=outcome.response.status_code,
            simulated_ids=outcome.simulated_ids,
        )
        return outcome.response
