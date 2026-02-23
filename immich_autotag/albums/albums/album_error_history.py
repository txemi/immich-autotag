from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from immich_autotag.albums.albums.album_error_entry import AlbumErrorEntry

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_api_exception_info import (
        AlbumApiExceptionInfo,
    )


class AlbumErrorHistory:
    """
    Encapsulates the error history for an album, including append, prune, count,
    and windowed count logic.
    """

    def __init__(self) -> None:
        self._errors: List[AlbumErrorEntry] = []

    def append(self, entry: AlbumErrorEntry) -> None:
        self._errors.append(entry)

    def append_api_exc(self, api_exc: "AlbumApiExceptionInfo") -> None:
        """Append an error entry from an AlbumApiExceptionInfo object and prune old
        entries."""
        import time

        from immich_autotag.config.internal_config import ALBUM_ERROR_WINDOW_SECONDS

        now = time.time()
        code = (
            f"HTTP_{api_exc.status_code}"
            if api_exc.status_code is not None
            else "API_ERROR"
        )
        msg = api_exc.message
        self.append(
            AlbumErrorEntry(
                timestamp=now,
                code=code,
                message=str(msg),
                api_exc=api_exc,
            )
        )
        # Prune old errors after appending
        cutoff = now - int(ALBUM_ERROR_WINDOW_SECONDS)
        self.prune(cutoff)

    def prune(self, cutoff: float) -> None:
        self._errors = [e for e in self._errors if e.timestamp >= cutoff]

    def count(self, since: Optional[float] = None) -> int:
        if since is None:
            return len(self._errors)
        return sum(1 for e in self._errors if e.timestamp >= since)

    def count_in_window(self, window_seconds: Optional[int] = None) -> int:
        """
        Returns the number of errors in the last `window_seconds` seconds.
        If window_seconds is None, uses the default window from config.
        """
        import time

        from immich_autotag.config.internal_config import ALBUM_ERROR_WINDOW_SECONDS

        window = (
            int(window_seconds)
            if window_seconds is not None
            else int(ALBUM_ERROR_WINDOW_SECONDS)
        )
        cutoff = time.time() - window
        return self.count(since=cutoff)

    def as_list(self) -> List[AlbumErrorEntry]:
        return list(self._errors)

    def __iter__(self):
        return iter(self._errors)

    def __len__(self) -> int:
        return len(self._errors)
