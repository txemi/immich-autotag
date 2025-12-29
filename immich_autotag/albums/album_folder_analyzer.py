from __future__ import annotations

from pathlib import Path

import attrs
from typeguard import typechecked


@attrs.define(auto_attribs=True, slots=True)
class AlbumFolderAnalyzer:

    original_path: Path = attrs.field(validator=attrs.validators.instance_of(Path))
    folders: list = attrs.field(
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
        path = (
            self.original_path
            if isinstance(self.original_path, Path)
            else Path(self.original_path)
        ).resolve()
        folders = [
            part
            for part in path.parts
            if part not in (path.root, path.anchor, "")
        ]
        # If the last component looks like a file (has an extension), remove it
        # todo: no entiendo la logica de abajo, si la ruta asumimos que es un fichero no es mejor coger todo menos el ultimo?
        if folders and re.search(r"\.[a-zA-Z0-9]{2,5}$", folders[-1]):
            folders = folders[:-1]
        self.folders = folders

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
    def _is_excluded_by_pattern(self) -> bool:
        """
        Returns True if the folder path matches any exclusion pattern.
        """
        import re
        from immich_autotag.config.user import ALBUM_DETECTION_EXCLUDED_PATHS
        # Compose the full folder path as a string (joined by /)
        folder_path_str = "/".join(self.folders).lower()
        for pattern in ALBUM_DETECTION_EXCLUDED_PATHS:
            if re.search(pattern, folder_path_str, re.IGNORECASE):
                return True
        return False
    @typechecked
    def get_album_name(self):
        if self._is_excluded_by_pattern():
            return None        
        import re

        SEPARATOR = "/"  # Cambia aquí para modificar el separador en todos los casos
        DATE_FORMAT_STR = "YYYY-MM-DD"
        MAX_ALBUM_DEPTH = 3  # Máximo de carpetas a concatenar tras la fecha

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
        # Si la carpeta de fecha está al final y es solo la fecha, ignorar
        folder_name = self.folders[idx]
        if idx == len(self.folders) - 1 and len(folder_name) == len(DATE_FORMAT_STR):
            return None
        # Concatenar desde la carpeta de fecha hasta un máximo de MAX_ALBUM_DEPTH carpetas siguientes
        end_idx = min(idx + 1 + MAX_ALBUM_DEPTH, len(self.folders))
        album_parts = self.folders[idx:end_idx]
        album_name = SEPARATOR.join(album_parts)
        if len(album_name) < 10:
            raise NotImplementedError(
                f"Detected album name is suspiciously short: '{album_name}'"
            )
        # Excluir por patrón en la ruta de carpetas

        return album_name
