from __future__ import annotations

from typing import Dict

import attrs

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.types.uuid_wrappers import AssetUUID


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class DuplicateAssetsInfo:
    # Maps asset AssetUUID to AssetResponseWrapper
    _mapping: Dict[AssetUUID, AssetResponseWrapper]

    def all_album_names(self) -> set[str]:
        """Return a set with all album names found among duplicates."""
        return {
            album
            for wrapper in self._mapping.values()
            for album in wrapper.get_album_names()
        }

    def get_details(self) -> Dict[AssetUUID, AssetResponseWrapper]:
        """Return the full mapping (read-only)."""
        return dict(self._mapping)
