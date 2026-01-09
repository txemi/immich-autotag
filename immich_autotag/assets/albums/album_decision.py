from __future__ import annotations

import re

import attrs

from immich_autotag.assets.duplicates._duplicate_albums_info import DuplicateAlbumsInfo


@attrs.define(auto_attribs=True, slots=True, frozen=True)
class AlbumDecision:
    """
    Encapsulates the decision logic for album assignment, including all album info from duplicates (as DuplicateAlbumsInfo)
    and the album detected from folder structure (if any).
    """

    duplicates_info: DuplicateAlbumsInfo
    album_from_folder: str | None

    def __attrs_post_init__(self):
        # Place breakpoint here for debugging construction
        pass

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
