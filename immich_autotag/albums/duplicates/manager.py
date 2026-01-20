"""Duplicate album manager.

This module centralizes duplicate-album handling: collection for later
inspection and an optional auto-merge flow which moves assets from a
duplicate album into the chosen existing album and deletes the duplicate.

The manager intentionally performs best-effort operations when running in
non-development modes: errors are logged and recorded but do not crash the run.
In DEVELOPMENT mode behavior remains fail-fast.
"""

from __future__ import annotations

from typing import List, Optional
import json
from uuid import UUID

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient


class DuplicateAlbumManager:
    def __init__(
        self,
        client: Optional[ImmichClient] = None,
        tag_mod_report: Optional[ModificationReport] = None,
    ) -> None:
        self.client = client
        self.tag_mod_report = tag_mod_report
        self._collected: List[dict] = []

        # Read config: DEFAULT_ERROR_MODE and optional DUPLICATE_AUTO_MERGE
        try:
            from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
            from immich_autotag.config._internal_types import ErrorHandlingMode
        except Exception:
            DEFAULT_ERROR_MODE = None
            ErrorHandlingMode = None

        try:
            # optional flag; if not present, default False
            from immich_autotag.config.internal_config import DUPLICATE_AUTO_MERGE
        except Exception:
            DUPLICATE_AUTO_MERGE = False

        self.default_error_mode = DEFAULT_ERROR_MODE
        self.ErrorHandlingMode = ErrorHandlingMode
        self.auto_merge_enabled = bool(DUPLICATE_AUTO_MERGE)

    def collect(
        self,
        existing: Optional[AlbumResponseWrapper],
        incoming: Optional[AlbumResponseWrapper],
        reason: str = "duplicate",
    ) -> None:
        """Record a duplicate occurrence for later operator inspection."""
        try:
            entry = {
                "timestamp": __import__("datetime").datetime.utcnow().isoformat() + "Z",
                "reason": reason,
                "existing": None,
                "incoming": None,
            }
            if existing is not None:
                try:
                    entry["existing"] = {
                        "id": existing.get_album_id(),
                        "name": existing.get_album_name(),
                        "asset_count": len(existing.get_asset_ids() or []),
                    }
                except Exception:
                    entry["existing"] = {"id": None, "name": None}
            if incoming is not None:
                try:
                    entry["incoming"] = {
                        "id": incoming.get_album_id(),
                        "name": incoming.get_album_name(),
                        "asset_count": len(incoming.get_asset_ids() or []),
                    }
                except Exception:
                    entry["incoming"] = {"id": None, "name": None}
            self._collected.append(entry)
        except Exception:
            # Best-effort; never raise to avoid breaking main flow
            return

    def get_collected(self) -> List[dict]:
        return list(self._collected)

    def write_summary(self) -> None:
        """Write collected duplicates to `run_output_dir/albums_duplicates_summary.json` (best-effort)."""
        try:
            from immich_autotag.utils.run_output_dir import get_run_output_dir

            out_dir = get_run_output_dir()
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / "albums_duplicates_summary.json"
            with out_file.open("w", encoding="utf-8") as fh:
                json.dump({"count": len(self._collected), "duplicates": self._collected}, fh, indent=2)
        except Exception:
            # Best-effort
            pass

    def auto_merge(self, existing: AlbumResponseWrapper, duplicate: AlbumResponseWrapper) -> bool:
        """Attempt to move assets from `duplicate` into `existing` and delete `duplicate`.

        Returns True if the merge completed (delete performed), False otherwise.

        Behavior:
        - If running in DEVELOPMENT mode, raises on unexpected errors.
        - In non-development, errors are logged and the function returns False.
        """
        # If auto-merge not enabled, bail out
        if not self.auto_merge_enabled:
            return False

        client = self.client
        if client is None:
            # Cannot perform server-side actions without client
            return False

        from immich_autotag.logging.utils import log
        from immich_autotag.logging.levels import LogLevel

        # Gather asset ids from duplicate
        try:
            asset_ids = list(duplicate.get_asset_ids() or [])
        except Exception:
            asset_ids = []

        if not asset_ids:
            # Nothing to move; just delete duplicate
            try:
                # Use AlbumCollectionWrapper to remove both server and local
                from immich_autotag.albums.album_collection_wrapper import (
                    AlbumCollectionWrapper,
                )

                coll = AlbumCollectionWrapper.get_instance()
                coll.remove_album(duplicate, client)
                if self.tag_mod_report:
                    from immich_autotag.tags.modification_kind import ModificationKind

                    self.tag_mod_report.add_album_modification(
                        kind=ModificationKind.DELETE_ALBUM,
                        album=duplicate,
                        extra={"reason": "auto_merge_empty"},
                    )
                log(f"Auto-merge: deleted empty duplicate album {duplicate.get_album_id()}", level=LogLevel.FOCUS)
                return True
            except Exception:
                if self.default_error_mode is not None and self.ErrorHandlingMode is not None:
                    if self.default_error_mode == self.ErrorHandlingMode.DEVELOPMENT:
                        raise
                log(f"Auto-merge: failed to delete empty duplicate album {duplicate.get_album_id()}", level=LogLevel.WARNING)
                return False

        # Convert to UUIDs
        uuids = []
        for aid in asset_ids:
            try:
                uuids.append(UUID(aid))
            except Exception:
                # Skip invalid ids
                continue

        if not uuids:
            return False

        # Perform add_assets_to_album for existing album
        try:
            from immich_client.api.albums import add_assets_to_album, remove_asset_from_album
            from immich_client.models.bulk_ids_dto import BulkIdsDto

            add_assets_to_album.sync(id=UUID(existing.get_album_id()), client=client, body=BulkIdsDto(ids=uuids))
            # Remove from duplicate
            remove_asset_from_album.sync(id=UUID(duplicate.get_album_id()), client=client, body=BulkIdsDto(ids=uuids))

            # Delete duplicate album
            from immich_autotag.albums.album_collection_wrapper import AlbumCollectionWrapper

            coll = AlbumCollectionWrapper.get_instance()
            coll.remove_album(duplicate, client)

            if self.tag_mod_report:
                from immich_autotag.tags.modification_kind import ModificationKind

                self.tag_mod_report.add_album_modification(
                    kind=ModificationKind.MERGE_ALBUMS,
                    album=existing,
                    extra={"merged_from": duplicate.get_album_id(), "moved_assets_count": len(uuids)},
                )

            log(
                f"Auto-merge: moved {len(uuids)} assets from album {duplicate.get_album_id()} into {existing.get_album_id()} and deleted duplicate.",
                level=LogLevel.FOCUS,
            )
            return True
        except Exception as e:
            # Respect error mode
            if self.default_error_mode is not None and self.ErrorHandlingMode is not None:
                if self.default_error_mode == self.ErrorHandlingMode.DEVELOPMENT:
                    raise
            try:
                log(f"Auto-merge failed for albums {duplicate.get_album_id()} -> {existing.get_album_id()}: {e}", level=LogLevel.WARNING)
            except Exception:
                pass
            # Collect a record for operator
            try:
                self.collect(existing=existing, incoming=duplicate, reason="auto_merge_failed")
            except Exception:
                pass
            return False
