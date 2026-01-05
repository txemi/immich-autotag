from __future__ import annotations

from typing import Dict
from uuid import UUID

import attrs

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAlbumsInfo:
    # Maps asset UUID to AssetResponseWrapper
    _mapping: Dict[UUID, AssetResponseWrapper]

    def all_album_names(self) -> set[str]:
        """Return a set with all album names found among duplicates."""
        return {
            album
            for wrapper in self._mapping.values()
            for album in wrapper.get_album_names()
        }

    def get_details(self) -> Dict[UUID, AssetResponseWrapper]:
        """Return the full mapping (read-only)."""
        return dict(self._mapping)
