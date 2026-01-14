from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
    from immich_autotag.assets.duplicates._duplicate_albums_info import (
        DuplicateAssetsInfo,
    )


@attrs.define(auto_attribs=True, slots=True)
class AlbumDecision:
    """
    Encapsulates the decision logic for album assignment with lazy evaluation.
    Receives the asset_wrapper and computes duplicates_info and album_from_folder only when needed.
    """

    asset_wrapper: "AssetResponseWrapper"

    def __attrs_post_init__(self):
        # Place breakpoint here for debugging construction
        pass

    @cached_property
    def duplicates_info(self) -> "DuplicateAssetsInfo":
        """Lazy computation of duplicates info."""
        from immich_autotag.assets.duplicates._get_album_from_duplicates import (
            get_duplicate_wrappers_info,
        )

        return get_duplicate_wrappers_info(self.asset_wrapper)

    @cached_property
    def album_from_folder(self) -> str | None:
        """Lazy computation of album from folder structure."""
        return self.asset_wrapper.try_detect_album_from_folders()

    def all_options(self) -> set[str]:
        opts = set(self.duplicates_info.all_album_names())
        from immich_autotag.classification.classification_rule_set import (
            ClassificationRuleSet,
        )

        rule_set = ClassificationRuleSet.get_rule_set_from_config_manager()
        opts = {a for a in opts if rule_set.matches_album(a)}
        if self.album_from_folder and rule_set.matches_album(self.album_from_folder):
            opts.add(self.album_from_folder)
        return opts

    def valid_albums(self) -> set[str]:
        # all_options() already filters by ALBUM_PATTERN
        return self.all_options()

    def is_unique(self) -> bool:
        valid = self.valid_albums()
        return len(valid) == 1

    def has_conflict(self) -> bool:
        valid = self.valid_albums()
        return len(valid) > 1

    def get_unique(self) -> str | None:
        valid = self.valid_albums()
        if len(valid) == 1:
            return next(iter(valid))
        return None

    def get_album_origin(self, album: str) -> str:
        if self.album_from_folder == album:
            return "from folders"
        elif album in self.duplicates_info.all_album_names():
            return "from duplicates"
        else:
            return "unknown"

    def __str__(self):
        return f"AlbumDecision(valid={self.valid_albums()}, folder={self.album_from_folder})"
