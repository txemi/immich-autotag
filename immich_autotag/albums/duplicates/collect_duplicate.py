from typing import Optional

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReports,
)


@typechecked
def collect_duplicate(
    _collected_duplicates: DuplicateAlbumReports,
    existing: Optional[AlbumResponseWrapper],
    incoming: Optional[AlbumResponseWrapper],
    reason: str = "duplicate_name",
) -> None:
    """Record a duplicate album occurrence for later operator inspection.

    Stores a small summary dict into `_collected_duplicates` (best-effort).
    """
    try:
        entry = {
            "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            "reason": reason,
            "existing": None,
            "incoming": None,
        }
        if existing is not None:
            try:
                report = DuplicateAlbumReport(
                    album_name=existing.get_album_name() if existing else "",
                    existing_album=existing,
                    incoming_album=incoming,
                    note=reason,
                )
                _collected_duplicates.append(report)
            except Exception:
                pass
    except Exception:
        # Best-effort; do not allow errors here to interrupt main flow
        return
