import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper


@attrs.define(auto_attribs=True, slots=True)
class UnavailableAlbums:
        def write_summary(self) -> None:
            """Write a small JSON summary of unavailable albums for operator inspection."""
            import json
            from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
            from immich_autotag.utils.run_output_dir import get_run_output_dir

            summary_items = []

            def _unavailable_sort_key(w: AlbumResponseWrapper) -> str:
                album_id = w.get_album_id()
                if not album_id:
                    raise RuntimeError(
                        f"Album missing valid id while writing unavailable summary: {w!r}"
                    )
                return album_id

            unavailable_sorted: list[AlbumResponseWrapper] = self.sorted(_unavailable_sort_key)  # type: ignore
            for wrapper in unavailable_sorted:
                album_id: str = wrapper.get_album_id()
                if not album_id:
                    raise RuntimeError(
                        f"Album missing valid id while building summary: {wrapper!r}"
                    )
                name: str = wrapper.get_album_name()
                summary_items.append({"id": album_id, "name": name})  # type: ignore

            out_dir = get_run_output_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "albums_unavailable_summary.json"

            try:
                with out_file.open("w", encoding="utf-8") as fh:
                    json.dump(
                        {"count": len(summary_items), "albums": summary_items}, fh, indent=2
                    )  # type: ignore
            except Exception:
                try:
                    if DEFAULT_ERROR_MODE.name == "DEVELOPMENT":
                        raise
                except AttributeError:
                    raise
                # else: swallow in production
    """
    Encapsulates tracking of unavailable albums and their count.
    """

    _albums: set[AlbumResponseWrapper] = attrs.field(
        factory=set, init=False, repr=False
    )

    def add(self, album: AlbumResponseWrapper) -> bool:
        if album in self._albums:
            return False
        self._albums.add(album)
        return True

    def __contains__(self, album: AlbumResponseWrapper) -> bool:
        return album in self._albums

    def __len__(self) -> int:
        return len(self._albums)

    @property
    def count(self) -> int:
        return len(self._albums)

    def sorted(self, key):
        return sorted(self._albums, key=key)

    def items(self):
        return self._albums
