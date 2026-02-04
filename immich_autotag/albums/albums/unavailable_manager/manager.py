from typing import TYPE_CHECKING

import attrs

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.unavailable_albums import UnavailableAlbums

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )


@attrs.define(auto_attribs=True, slots=True)
class UnavailableAlbumManager:
    """
    Encapsulates all logic for managing unavailable albums:
    - Tracking unavailable albums
    - Evaluating global policy/threshold
    - Reporting and summary
    """

    _collection: "AlbumCollectionWrapper"
    _unavailable: UnavailableAlbums = attrs.Factory(UnavailableAlbums)

    def _evaluate_global_policy(self) -> None:
        """Evaluate global unavailable-albums policy and act according to config."""
        from immich_autotag.config.internal_config import GLOBAL_UNAVAILABLE_THRESHOLD
        from immich_autotag.report.modification_kind import ModificationKind
        from immich_autotag.report.modification_report import ModificationReport

        threshold = int(GLOBAL_UNAVAILABLE_THRESHOLD)
        if not self._unavailable.count >= threshold:
            return
        from immich_autotag.config.dev_mode import is_development_mode

        if is_development_mode():
            raise RuntimeError(
                f"Too many albums marked unavailable during run: "
                f"{self._unavailable.count} >= {threshold}. "
                f"Failing fast (DEVELOPMENT mode)."
            )
        tag_mod_report = ModificationReport.get_instance()
        tag_mod_report.add_error_modification(
            kind=ModificationKind.ERROR_ALBUM_NOT_FOUND,
            error_message=(
                f"global unavailable threshold exceeded: "
                f"{self._unavailable.count} >= {threshold}"
            ),
            error_category="GLOBAL_THRESHOLD",
            extra={
                "unavailable_count": self._unavailable.count,
                "threshold": threshold,
            },
        )
        self._unavailable.write_summary()

    def notify_album_marked_unavailable(
        self, album_wrapper: AlbumResponseWrapper
    ) -> None:
        """Notify manager that an album was marked unavailable."""
        added = self._unavailable.add(album_wrapper)
        if not added:
            return
        # Logging and policy evaluation delegated to global policy method
        self._evaluate_global_policy()
