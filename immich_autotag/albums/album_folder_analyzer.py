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
        default=r"^\d{4}-\d{2}-\d{2}$",
        validator=attrs.validators.instance_of(str),
    )

    def __attrs_post_init__(self):
        import re

        # Convert to Path if not already
        path = (
            self.original_path
            if isinstance(self.original_path, Path)
            else Path(self.original_path)
        )
        # Get all parts except root
        folders = [
            part
            for part in path.parts
            if part not in (path.root, path.anchor, ".", "..", "")
        ]
        # If the last component looks like a file (has an extension), remove it
        if folders and re.search(r"\.[a-zA-Z0-9]{2,5}$", folders[-1]):
            folders = folders[:-1]
        self.folders = folders

    def date_folder_indices(self):
        import re

        return [
            i for i, f in enumerate(self.folders) if re.fullmatch(self.date_pattern, f)
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
    def get_album_name(self):
        import re

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
                    return f
            return None
        # >1 date folders: ambiguous, not supported
        if self.num_date_folders() > 1:
            idxs = self.date_folder_indices()
            raise NotImplementedError(
                f"Multiple candidate folders for album detection: {[self.folders[i] for i in idxs]}"
            )
        # 1 date folder
        idx = self.date_folder_indices()[0]
        if idx == len(self.folders) - 1:
            # --- Lógica especial para carpeta con fecha en última posición ---
            # Si la única carpeta con formato de fecha está al final del path:
            #   - Si la carpeta es exactamente la fecha (sin más caracteres), lo ignoramos y devolvemos None.
            #     Esto ocurre frecuentemente en carpetas generadas por apps como WhatsApp y no es útil para crear álbumes.
            #   - Si la carpeta tiene la fecha y más caracteres, comprobamos que la longitud sea suficiente (fecha + 10).
            #     Si cumple, devolvemos el nombre de la carpeta como nombre de álbum.
            #     Si no, lanzamos una excepción para analizar el caso.
            folder_name = self.folders[idx]
            if len(folder_name) == len("YYYY-MM-DD"):
                # Solo la fecha, caso común de carpetas de WhatsApp, ignorar
                return None
            min_length = 10 + len("YYYY-MM-DD")  # fecha + 10
            if len(folder_name) < min_length:
                raise NotImplementedError(
                    f"Detected album name is suspiciously short (date folder at end): '{folder_name}'"
                )
            return folder_name
        if idx == len(self.folders) - 2:
            # Date folder is penultimate: concatena con la última
            album_name = f"{self.folders[idx]} {self.folders[idx+1]}"
            if len(album_name) < 10:
                raise NotImplementedError(
                    f"Detected album name is suspiciously short: '{album_name}'"
                )
            return album_name
        if idx == len(self.folders) - 3:
            # --- Nuevo caso: carpeta con fecha en antepenúltima posición ---
            # Si la carpeta con fecha está en la antepenúltima posición, concatenamos esa carpeta y las dos siguientes.
            # Esto permite capturar rutas como .../fecha/fecha-descriptivo/picasa/Evento/...
            album_name = f"{self.folders[idx]} {self.folders[idx+1]} {self.folders[idx+2]}"
            if len(album_name) < 10:
                raise NotImplementedError(
                    f"Detected album name is suspiciously short: '{album_name}'"
                )
            return album_name
        # Date folder in other position: not supported for now
        return None
