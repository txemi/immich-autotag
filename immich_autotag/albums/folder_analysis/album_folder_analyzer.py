from __future__ import annotations

from pathlib import Path

import attrs
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AlbumFolderAnalyzer:
    """
    Analyzes a folder path to determine album-related metadata and naming.

    Responsibility:
        - Parses and processes a given filesystem path to extract folder components relevant for album detection.
        - Identifies date-based folders and their positions to infer album structure.
        - Applies exclusion patterns to filter out unwanted paths.
        - Provides methods to determine if a path is ambiguous, excluded, or suitable for album creation.
        - Generates a candidate album name based on configurable rules and folder structure.

    Usage:
        Instantiate with a Path object representing the original folder or file path. Use the provided methods to analyze the path and extract album information for further processing or album creation workflows.
    """

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

        for pattern in manager.config.album_detection_from_folders.excluded_paths:
            if re.search(pattern, folder_path_str, re.IGNORECASE):
                return True
        return False

    @typechecked
    def has_multiple_candidate_folders(self) -> bool:
        """
        Returns True if there are multiple date folders (which create ambiguity for album detection).
        """
        return self.num_date_folders() > 1

    @typechecked
    def get_candidate_folders(self) -> list[str]:
        """
        Returns the list of candidate folders if has_multiple_candidate_folders() is True.
        """
        if self.has_multiple_candidate_folders():
            idxs = self.date_folder_indices()
            return [self.folders[i] for i in idxs]
        return []

    @typechecked
    def get_album_name(self):
        """
        Determines the album name based on the folder path analysis.

        Responsibility:
            - Extracts a suitable album name from the folder structure, following these rules:
                * If the folder path matches an exclusion pattern, returns None.
                * If there are zero date folders, looks for a folder starting with a date prefix but not only the date; if found, raises NotImplementedError for suspiciously short names.
                * If there are multiple date folders, returns None (ambiguous case, to be handled by the caller).
                * If there is exactly one date folder, constructs the album name by concatenating up to MAX_ALBUM_DEPTH folders starting from the date folder, separated by SEPARATOR. If the resulting name is suspiciously short, raises NotImplementedError.
            - Returns None if no valid album name can be determined.
        """
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
        # >1 date folders: ambiguous, not supported - return None and let caller handle it
        if self.num_date_folders() > 1:
            return None
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
