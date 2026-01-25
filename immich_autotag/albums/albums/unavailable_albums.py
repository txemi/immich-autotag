from typing import Callable

import attrs
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class UnavailableAlbums:
    """
    Encapsulates tracking of unavailable albums and their count.
    """

    _albums: set[AlbumResponseWrapper] = attrs.field(
        factory=lambda: set(), init=False, repr=False
    )

    def add(self, album: AlbumResponseWrapper) -> bool:
        if album in self._albums:
            return False
        self._albums.add(album)
        return True

    @property
    def count(self) -> int:
        return len(self._albums)

    @typechecked
    def sorted(
        self, key: Callable[[AlbumResponseWrapper], str]
    ) -> list[AlbumResponseWrapper]:
        return sorted(self._albums, key=key)

    def items(self):
        return self._albums

    @typechecked
    def write_summary(self) -> None:
        """Write a small JSON summary of unavailable albums for operator inspection.

        Behavior:
        - The function returns `None` (it's a side-effecting writer).
        - The helper `_unavailable_sort_key` returns a string used for sorting.
        - If an unavailable album lacks an ID or retrieving the name/id raises,
          this is considered a programming/data error and the function will
          raise so the problem is surfaced (fail-fast).
        - Only filesystem/write errors when persisting the summary are
          swallowed in PRODUCTION mode; in DEVELOPMENT they will propagate.
        """
        import json

        # Import error-mode config so we can decide whether to swallow IO errors
        # Fail-fast: configuration symbols must exist; let ImportError propagate.
        from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
        from immich_autotag.utils.run_output_dir import get_run_output_dir

        summary_items: list[dict[str, str]] = []

        def _unavailable_sort_key(w: AlbumResponseWrapper) -> str:
            album_id = str(w.get_album_uuid())
            if not album_id:
                raise RuntimeError(
                    f"Album missing valid id while writing unavailable summary: {w!r}"
                )
            return album_id

        unavailable_sorted: list[AlbumResponseWrapper] = self.sorted(
            _unavailable_sort_key
        )
        for wrapper in unavailable_sorted:
            album_id: str = str(wrapper.get_album_uuid())
            if not album_id:
                raise RuntimeError(
                    f"Album missing valid id while building summary: {wrapper!r}"
                )
            name: str = wrapper.get_album_name()
            summary_items.append({"id": album_id, "name": name})

        out_dir = get_run_output_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "albums_unavailable_summary.json"

        try:
            with out_file.open("w", encoding="utf-8") as fh:
                json.dump(
                    {"count": len(summary_items), "albums": summary_items}, fh, indent=2
                )
        except Exception:
            # In DEVELOPMENT we want to see IO problems; in PRODUCTION se traga el error
            try:
                if DEFAULT_ERROR_MODE.name == "DEVELOPMENT":
                    raise
            except AttributeError:
                raise
            # else: swallow in production

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album in self._albums

    def __len__(self) -> int:
        return len(self._albums)
