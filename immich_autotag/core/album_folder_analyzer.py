import attrs
from pathlib import Path
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
        path = (
            self.original_path
            if isinstance(self.original_path, Path)
            else Path(self.original_path)
        )
        folders = [
            part
            for part in path.parts
            if part not in (path.root, path.anchor, ".", "..", "")
        ]
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
        if self.num_date_folders() > 1:
            idxs = self.date_folder_indices()
            raise NotImplementedError(
                f"Multiple candidate folders for album detection: {[self.folders[i] for i in idxs]}"
            )
        idx = self.date_folder_indices()[0]
        if idx == len(self.folders) - 1:
            return None
        if idx == len(self.folders) - 2:
            album_name = f"{self.folders[idx]} {self.folders[idx+1]}"
            if len(album_name) < 10:
                raise NotImplementedError(
                    f"Detected album name is suspiciously short: '{album_name}'"
                )
            return album_name
        return None
