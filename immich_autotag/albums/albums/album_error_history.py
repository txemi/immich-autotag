from __future__ import annotations
from typing import List, Optional
from immich_autotag.albums.albums.album_error_entry import AlbumErrorEntry

class AlbumErrorHistory:
    """
    Encapsulates the error history for an album, including append, prune, and count logic.
    """
    def __init__(self) -> None:
        self._errors: List[AlbumErrorEntry] = []

    def append(self, entry: AlbumErrorEntry) -> None:
        self._errors.append(entry)

    def prune(self, cutoff: float) -> None:
        self._errors = [e for e in self._errors if e.timestamp >= cutoff]

    def count(self, since: Optional[float] = None) -> int:
        if since is None:
            return len(self._errors)
        return sum(1 for e in self._errors if e.timestamp >= since)

    def as_list(self) -> List[AlbumErrorEntry]:
        return list(self._errors)

    def __len__(self) -> int:
        return len(self._errors)

    def __iter__(self):
        return iter(self._errors)
