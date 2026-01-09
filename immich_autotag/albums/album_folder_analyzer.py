from __future__ import annotations

from pathlib import Path

import attrs
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AlbumFolderAnalyzer:

    original_path: Path = attrs.field(validator=attrs.validators.instance_of(Path))
    folders: list[str] = attrs.field(
        init=False, validator=attrs.validators.instance_of(list)
    )
    date_pattern: str = attrs.field(
        init=False,
        default=r"^\d{4}-\d{2}-\d{2}",
        validator=attrs.validators.instance_of(str),
    )

    def __attrs_post_init__(self):
        import re

        # Convert to Path if not already and resolve to canonical path (removes '.', '..', etc)
        path = self.original_path.resolve()
        folders = [
            part for part in path.parts if part not in (path.root, path.anchor, "")
        ]
        # If the last component looks like a file (has an extension), remove it
        # todo: I don't understand the logic below, if we assume the path is a file isn't it better to take everything except the last one?
        if folders and re.search(r"\.[a-zA-Z0-9]{2,5}$", folders[-1]):
            folders = folders[:-1]
        self.folders = folders

    @typechecked
    def date_folder_indices(self):
        import re

        date_prefix_pattern = r"^\d{4}-\d{2}-\d{2}"
        return [
            i for i, f in enumerate(self.folders) if re.match(date_prefix_pattern, f)
        ]

    @typechecked
    def num_date_folders(self):
        return len(self.date_folder_indices())

    @typechecked
    def is_date_in_last_position(self):
        idxs = self.date_folder_indices()
        return len(idxs) == 1 and idxs[0] == len(self.folders) - 1

    @typechecked
    def is_date_in_penultimate_position(self):
        idxs = self.date_folder_indices()
        return len(idxs) == 1 and idxs[0] == len(self.folders) - 2

    @typechecked
    def _is_excluded_by_pattern(self) -> bool:
        """
        Returns True if the folder path matches any exclusion pattern.
        """
        import re

        # Compose the full folder path as a string (joined by /)
        folder_path_str = "/".join(self.folders).lower()
        from immich_autotag.config.manager import ConfigManager

        manager = ConfigManager.get_instance()
        if not manager or not manager.config or not manager.config.features:
            raise RuntimeError("ConfigManager or features config not initialized")
        for (
            pattern
        ) in manager.config.features.album_detection_from_folders.excluded_paths:
            if re.search(pattern, folder_path_str, re.IGNORECASE):
                return True
        return False

    @typechecked
    def get_album_name(self):
        if self._is_excluded_by_pattern():
            return None
        import re

        SEPARATOR = "/"  # Change here to modify the separator in all cases
        DATE_FORMAT_STR = "YYYY-MM-DD"
        MAX_ALBUM_DEPTH = 3  # Maximum folders to concatenate after the date

        # 0 date folders: look for folder starting with date (but not only date)
        if self.num_date_folders() == 0:
            date_prefix_pattern = r"^\d{4}-\d{2}-\d{2}"
            for f in self.folders:
                if re.match(date_prefix_pattern, f) and not re.fullmatch(
                    self.date_pattern, f
                ):
                    if len(f) < 10:
                        raise NotImplementedError(
                            f"Detected album name is suspiciously short: '{f}'"
                        )
                    raise NotImplementedError
            return None
        # >1 date folders: ambiguous, not supported
        if self.num_date_folders() > 1:
            idxs = self.date_folder_indices()
            raise NotImplementedError(
                f"Multiple candidate folders for album detection: {[self.folders[i] for i in idxs]}"
            )
        # 1 date folder
        idx = self.date_folder_indices()[0]
        # If the date folder is at the end and is only the date, ignore it
        folder_name = self.folders[idx]
        if idx == len(self.folders) - 1 and len(folder_name) == len(DATE_FORMAT_STR):
            return None
        # Concatenate from the date folder up to a maximum of MAX_ALBUM_DEPTH following folders
        end_idx = min(idx + 1 + MAX_ALBUM_DEPTH, len(self.folders))
        album_parts = self.folders[idx:end_idx]
        album_name = SEPARATOR.join(album_parts)
        if len(album_name) < 10:
            raise NotImplementedError(
                f"Detected album name is suspiciously short: '{album_name}'"
            )
        # Exclude by pattern in folder path

        return album_name
