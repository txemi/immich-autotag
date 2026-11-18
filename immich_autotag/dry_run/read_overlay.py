"""
Keeps reads coherent with the writes a dry run did not send.

Two cases:

- a read about an entity that only exists in the simulation (an album or a tag
  with a simulated id), or that the simulation deleted, is answered here and
  never reaches Immich (``answer_locally``);
- a read Immich answers is patched with the simulated changes (``patch``): the
  album list gains the simulated albums, an asset shows its simulated date and
  tags, an album search shows the assets that were "added" to it.
"""

from __future__ import annotations

import re
from typing import Any

import httpx

from immich_autotag.dry_run.http_helpers import (
    OVERLAY,
    error_response,
    json_response,
    read_json_body,
    read_json_response,
    string_list,
)
from immich_autotag.dry_run.simulated_state import SimulatedState, is_simulated_id
from immich_autotag.dry_run.upstream_reader import UpstreamReader

_ALBUM_PATH = re.compile(r"^/albums/([^/]+)$")
_TAG_PATH = re.compile(r"^/tags/([^/]+)$")
_ASSET_PATH = re.compile(r"^/assets/([^/]+)$")
_UUID = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# UpdateAssetDto field -> where it lives in AssetResponseDto.
_ASSET_TOP_LEVEL_FIELDS = frozenset({"isFavorite", "visibility", "livePhotoVideoId"})
_ASSET_EXIF_FIELDS = frozenset(
    {"dateTimeOriginal", "description", "rating", "latitude", "longitude"}
)


def empty_search_result(items: list[dict[str, Any]]) -> dict[str, Any]:
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


def _visibility_matches(body: dict[str, Any], asset: dict[str, Any]) -> bool:
    wanted = body.get("visibility")
    if not isinstance(wanted, str):
        return True
    return asset.get("visibility") == wanted


class ReadOverlay:
    def __init__(self, *, state: SimulatedState, upstream: UpstreamReader) -> None:
        self._state = state
        self._upstream = upstream

    def _overlay_asset_tags(
        self, template: httpx.Request, asset_id: str, tags: list[Any]
    ) -> list[Any]:
        removed = self._state.tags_removed_from_asset(asset_id)
        result = [
            tag
            for tag in tags
            if not (isinstance(tag, dict) and tag.get("id") in removed)
        ]
        present = {tag.get("id") for tag in result if isinstance(tag, dict)}
        for tag_id in self._state.tags_added_to_asset(asset_id):
            if tag_id in present or self._state.is_deleted(tag_id):
                continue
            tag = self._state.get_simulated_tag(tag_id)
            if tag is None:
                tag = self._upstream.get_json(template, f"/tags/{tag_id}")
            if isinstance(tag, dict):
                result.append(tag)
        return result

    # --- assets -------------------------------------------------------------

    def apply_asset_overlay(
        self, template: httpx.Request, asset: dict[str, Any], *, with_tags: bool
    ) -> dict[str, Any]:
        """The asset as it would be after the simulated changes."""
        asset_id = asset.get("id")
        if not isinstance(asset_id, str):
            return asset
        patched = dict(asset)
        overrides = self._state.get_asset_overrides(asset_id)
        exif_changes = {k: v for k, v in overrides.items() if k in _ASSET_EXIF_FIELDS}
        for key, value in overrides.items():
            if key in _ASSET_TOP_LEVEL_FIELDS:
                patched[key] = value
        exif = patched.get("exifInfo")
        if exif_changes and isinstance(exif, dict):
            exif = dict(exif)
            exif.update(exif_changes)
            patched["exifInfo"] = exif
        tags = patched.get("tags")
        if with_tags and isinstance(tags, list):
            patched["tags"] = self._overlay_asset_tags(template, asset_id, tags)
        return patched

    def fetch_asset(
        self, template: httpx.Request, asset_id: str
    ) -> dict[str, Any] | None:
        asset = self._upstream.get_json(template, f"/assets/{asset_id}")
        if not isinstance(asset, dict):
            return None
        return self.apply_asset_overlay(template, asset, with_tags=True)

    def _answer_search_locally(self, request: httpx.Request) -> httpx.Response | None:
        body = read_json_body(request)
        if not isinstance(body, dict):
            return None
        containers = string_list(body.get("albumIds")) + string_list(body.get("tagIds"))
        if not any(is_simulated_id(c) or self._state.is_deleted(c) for c in containers):
            return None
        members: set[str] | None = None
        for container in containers:
            if is_simulated_id(container) and not self._state.is_deleted(container):
                current = self._state.get_added_members(container)
            else:
                current = set()
            members = current if members is None else members & current
        wanted = sorted(members or set())
        asset_filter = body.get("id")
        if isinstance(asset_filter, str):
            wanted = [a for a in wanted if a == asset_filter]
        items = []
        for asset_id in wanted:
            asset = self.fetch_asset(request, asset_id)
            if asset is not None and _visibility_matches(body, asset):
                items.append(asset)
        return json_response(200, empty_search_result(items))

    # --- answered here, never sent ------------------------------------------

    def answer_locally(
        self, request: httpx.Request, relative_path: str
    ) -> httpx.Response | None:
        method = request.method.upper()
        if relative_path.startswith("/search/") and method == "POST":
            return self._answer_search_locally(request)
        if method != "GET":
            return None
        album = _ALBUM_PATH.match(relative_path)
        if album and is_simulated_id(album.group(1)):
            found = self._state.get_simulated_album(album.group(1))
            if found is None or self._state.is_deleted(album.group(1)):
                return error_response(404, "Album not found (dry-run simulation)")
            return json_response(200, found)
        tag = _TAG_PATH.match(relative_path)
        if tag and is_simulated_id(tag.group(1)):
            found_tag = self._state.get_simulated_tag(tag.group(1))
            if found_tag is None or self._state.is_deleted(tag.group(1)):
                return error_response(404, "Tag not found (dry-run simulation)")
            return json_response(200, found_tag)
        if any(is_simulated_id(value) for value in _UUID.findall(str(request.url))):
            return error_response(
                404, "Entity only exists in the dry-run simulation: no data"
            )
        return None

    def _patch_json(self, response: httpx.Response, change: Any) -> httpx.Response:
        data = read_json_response(response)
        if data is None:
            return response
        return json_response(response.status_code, change(data), marker=OVERLAY)

    def _patch_album_list(self, data: Any) -> Any:
        if not isinstance(data, list):
            return data
        result = []
        for album in data:
            if not isinstance(album, dict):
                result.append(album)
                continue
            self._state.learn_album(album)
            if self._state.is_deleted(str(album.get("id"))):
                continue
            result.append(self._state.apply_album_overrides(album))
        result.extend(self._state.list_simulated_albums())
        return result

    def _patch_tag_list(self, data: Any) -> Any:
        if not isinstance(data, list):
            return data
        result = []
        for tag in data:
            if isinstance(tag, dict):
                self._state.learn_tag(tag)
                if self._state.is_deleted(str(tag.get("id"))):
                    continue
            result.append(tag)
        result.extend(self._state.list_simulated_tags())
        return result

    def _patch_album(self, response: httpx.Response) -> httpx.Response:
        data = read_json_response(response)
        if not isinstance(data, dict):
            return response
        self._state.learn_album(data)
        if self._state.is_deleted(str(data.get("id"))):
            return error_response(404, "Album deleted in the dry-run simulation")
        return json_response(200, self._state.apply_album_overrides(data), OVERLAY)

    def _overlay_membership(
        self,
        request: httpx.Request,
        body: dict[str, Any],
        container: str,
        items: list[Any],
        assets: dict[str, Any],
    ) -> list[Any]:
        removed = self._state.get_removed_members(container)
        result = [
            item
            for item in items
            if not (isinstance(item, dict) and item.get("id") in removed)
        ]
        present = {item.get("id") for item in result if isinstance(item, dict)}
        asset_filter = body.get("id")
        added = sorted(self._state.get_added_members(container) - present)
        if isinstance(asset_filter, str):
            added = [a for a in added if a == asset_filter]
        elif assets.get("nextPage"):
            # Simulated members go after the last real page.
            added = []
        for asset_id in added:
            asset = self.fetch_asset(request, asset_id)
            if asset is not None and _visibility_matches(body, asset):
                result.append(asset)
        return result

    def _patch_search(
        self, request: httpx.Request, response: httpx.Response
    ) -> httpx.Response:
        data = read_json_response(response)
        body = read_json_body(request)
        if not isinstance(data, dict) or not isinstance(body, dict):
            return response
        assets = data.get("assets")
        if not isinstance(assets, dict) or not isinstance(assets.get("items"), list):
            return response
        items = [
            (
                self.apply_asset_overlay(request, item, with_tags=False)
                if isinstance(item, dict)
                else item
            )
            for item in assets["items"]
        ]
        containers = string_list(body.get("albumIds")) + string_list(body.get("tagIds"))
        if len(containers) == 1 and self._state.has_membership_changes(containers[0]):
            items = self._overlay_membership(
                request, body, containers[0], items, assets
            )
        patched_assets = dict(assets)
        patched_assets["items"] = items
        patched_assets["count"] = len(items)
        patched = dict(data)
        patched["assets"] = patched_assets
        return json_response(200, patched, marker=OVERLAY)

    # --- sent, then patched -------------------------------------------------

    def patch(
        self, request: httpx.Request, relative_path: str, response: httpx.Response
    ) -> httpx.Response:
        if response.status_code != 200:
            return response
        method = request.method.upper()
        if method == "GET" and relative_path == "/albums":
            return self._patch_json(response, self._patch_album_list)
        if method == "GET" and relative_path == "/tags":
            return self._patch_json(response, self._patch_tag_list)
        if method == "GET" and _ALBUM_PATH.match(relative_path):
            return self._patch_album(response)
        if method == "GET" and _TAG_PATH.match(relative_path):
            data = read_json_response(response)
            if isinstance(data, dict):
                self._state.learn_tag(data)
            return response
        if method == "GET" and _ASSET_PATH.match(relative_path):
            return self._patch_json(
                response,
                lambda data: (
                    self.apply_asset_overlay(request, data, with_tags=True)
                    if isinstance(data, dict)
                    else data
                ),
            )
        if method == "POST" and relative_path.startswith("/search/"):
            return self._patch_search(request, response)
        return response
