"""
What Immich would look like after the writes a dry run did not send.

Later reads in the same run must stay coherent with those writes: an album that
was "created" must be found again, an asset "added" to an album must appear in
it. This object keeps that overlay. It never talks to Immich.

Ids of entities that only exist in the simulation (an album or a tag that would
be created) are valid UUIDs with a fixed, recognisable prefix: see
SIMULATED_ID_PREFIX.
"""

from __future__ import annotations

from typing import Any

# Version nibble 4 and variant 8 keep the value a valid UUID; the leading zeros
# and the "d7d7" group make it easy to spot in logs and in the changes file.
SIMULATED_ID_PREFIX = "00000000-d7d7-4000-8000-"


def is_simulated_id(value: str) -> bool:
    return value.lower().startswith(SIMULATED_ID_PREFIX)


class SimulatedState:
    """Overlay of the writes a dry run intercepted."""

    def __init__(self) -> None:
        self._next_id = 1
        self._albums: dict[str, dict[str, Any]] = {}
        self._tags: dict[str, dict[str, Any]] = {}
        self._tag_ids: set[str] = set()
        self._album_names: dict[str, str] = {}
        self._album_overrides: dict[str, dict[str, Any]] = {}
        self._deleted: set[str] = set()
        self._added: dict[str, set[str]] = {}
        self._removed: dict[str, set[str]] = {}
        self._asset_overrides: dict[str, dict[str, Any]] = {}
        self._album_template: dict[str, Any] | None = None
        self._tag_template: dict[str, Any] | None = None

    # --- simulated ids -------------------------------------------------------

    def new_simulated_id(self) -> str:
        value = f"{SIMULATED_ID_PREFIX}{self._next_id:012x}"
        self._next_id += 1
        return value

    # --- templates learned from real reads ----------------------------------

    def learn_album(self, album: dict[str, Any]) -> None:
        """Remembers the name of a real album (and its shape, as a template)."""
        album_id = album.get("id")
        name = album.get("albumName")
        if isinstance(album_id, str) and isinstance(name, str):
            if album_id not in self._album_names:
                self._album_names[album_id] = name
        if self._album_template is None:
            self._album_template = dict(album)

    def learn_tag(self, tag: dict[str, Any]) -> None:
        tag_id = tag.get("id")
        if isinstance(tag_id, str):
            self._tag_ids.add(tag_id)
        if self._tag_template is None:
            self._tag_template = dict(tag)

    def get_album_template(self) -> dict[str, Any] | None:
        return None if self._album_template is None else dict(self._album_template)

    def get_tag_template(self) -> dict[str, Any] | None:
        return None if self._tag_template is None else dict(self._tag_template)

    # --- albums -------------------------------------------------------------

    def add_simulated_album(self, album: dict[str, Any]) -> None:
        album_id = str(album["id"])
        self._albums[album_id] = album
        self._album_names[album_id] = str(album.get("albumName", ""))

    def get_simulated_album(self, album_id: str) -> dict[str, Any] | None:
        album = self._albums.get(album_id)
        if album is None:
            return None
        result = dict(album)
        result["assetCount"] = len(self._added.get(album_id, set()))
        return result

    def list_simulated_albums(self) -> list[dict[str, Any]]:
        result = []
        for album_id in self._albums:
            if album_id in self._deleted:
                continue
            album = self.get_simulated_album(album_id)
            if album is not None:
                result.append(album)
        return result

    def get_album_name(self, album_id: str) -> str | None:
        return self._album_names.get(album_id)

    def override_album(self, album_id: str, fields: dict[str, Any]) -> None:
        if album_id in self._albums:
            self._albums[album_id].update(fields)
        else:
            self._album_overrides.setdefault(album_id, {}).update(fields)
        name = fields.get("albumName")
        if isinstance(name, str):
            self._album_names[album_id] = name

    def apply_album_overrides(self, album: dict[str, Any]) -> dict[str, Any]:
        album_id = album.get("id")
        if not isinstance(album_id, str):
            return album
        overrides = self._album_overrides.get(album_id)
        if not overrides:
            return album
        patched = dict(album)
        patched.update(overrides)
        return patched

    # --- tags ---------------------------------------------------------------

    def add_simulated_tag(self, tag: dict[str, Any]) -> None:
        tag_id = str(tag["id"])
        self._tags[tag_id] = tag
        self._tag_ids.add(tag_id)

    def get_simulated_tag(self, tag_id: str) -> dict[str, Any] | None:
        tag = self._tags.get(tag_id)
        return None if tag is None else dict(tag)

    def list_simulated_tags(self) -> list[dict[str, Any]]:
        return [
            dict(tag) for key, tag in self._tags.items() if key not in self._deleted
        ]

    def mark_as_tag(self, entity_id: str) -> None:
        self._tag_ids.add(entity_id)

    def is_tag(self, entity_id: str) -> bool:
        return entity_id in self._tag_ids

    # --- deletions ----------------------------------------------------------

    def mark_deleted(self, entity_id: str) -> None:
        self._deleted.add(entity_id)

    def is_deleted(self, entity_id: str) -> bool:
        return entity_id in self._deleted

    # --- membership: assets in albums and tags on assets --------------------

    def add_members(self, container_id: str, asset_ids: list[str]) -> list[str]:
        """Adds assets to an album or a tag. Returns the ids already added before."""
        added = self._added.setdefault(container_id, set())
        removed = self._removed.setdefault(container_id, set())
        duplicates = [a for a in asset_ids if a in added]
        for asset_id in asset_ids:
            added.add(asset_id)
            removed.discard(asset_id)
        return duplicates

    def remove_members(self, container_id: str, asset_ids: list[str]) -> None:
        added = self._added.setdefault(container_id, set())
        removed = self._removed.setdefault(container_id, set())
        for asset_id in asset_ids:
            added.discard(asset_id)
            removed.add(asset_id)

    def get_added_members(self, container_id: str) -> set[str]:
        return set(self._added.get(container_id, set()))

    def get_removed_members(self, container_id: str) -> set[str]:
        return set(self._removed.get(container_id, set()))

    def has_membership_changes(self, container_id: str) -> bool:
        return bool(self._added.get(container_id) or self._removed.get(container_id))

    def tags_added_to_asset(self, asset_id: str) -> list[str]:
        return sorted(
            tag_id
            for tag_id, members in self._added.items()
            if tag_id in self._tag_ids and asset_id in members
        )

    def tags_removed_from_asset(self, asset_id: str) -> set[str]:
        return {
            tag_id
            for tag_id, members in self._removed.items()
            if tag_id in self._tag_ids and asset_id in members
        }

    # --- assets -------------------------------------------------------------

    def override_asset(self, asset_id: str, fields: dict[str, Any]) -> None:
        self._asset_overrides.setdefault(asset_id, {}).update(fields)

    def get_asset_overrides(self, asset_id: str) -> dict[str, Any]:
        return dict(self._asset_overrides.get(asset_id, {}))
