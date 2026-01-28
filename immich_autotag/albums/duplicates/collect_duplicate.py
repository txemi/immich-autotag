from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.duplicates.duplicate_album_reports import (
    DuplicateAlbumReport,
    DuplicateAlbumReports,
)


@typechecked
def collect_duplicate(
    _collected_duplicates: DuplicateAlbumReports,
    existing: AlbumResponseWrapper,
    incoming: AlbumResponseWrapper,
    reason: str = "duplicate_name",
) -> None:
    """Record a duplicate album occurrence for later operator inspection.

    Stores a small summary dict into `_collected_duplicates` (best-effort).
    """

    if existing is not None and incoming is not None:
        report = DuplicateAlbumReport(
            album_name=existing.get_album_name() if existing else "",
            existing_album=existing,
            incoming_album=incoming,
            note=reason,
        )
        _collected_duplicates.append(report)
