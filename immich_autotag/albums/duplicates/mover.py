"""Move assets between two albums (one-by-one).

Provides a single helper function that moves assets from a source album
wrapper into a destination album wrapper by adding each asset to the
destination and removing it from the source. The operation is performed
one asset at a time and records modifications in `ModificationReport` if
provided. Behavior respects `DEFAULT_ERROR_MODE` (fail-fast in
DEVELOPMENT).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from immich_autotag.albums.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient

@typechecked
def move_assets_between_albums(
    dest: AlbumResponseWrapper,
    src: AlbumResponseWrapper,
    client: ImmichClient,
    tag_mod_report: Optional[ModificationReport] = None,
) -> int:
    """Move assets from `src` album into `dest` album one-by-one.

    Returns the number of assets successfully moved.

    Raises RuntimeError in DEVELOPMENT mode on unexpected API failures.
    In non-development modes failures are logged and the function attempts
    to continue.
    """
    # Local imports to avoid circular dependencies at module import time
    from immich_client.api.albums import add_assets_to_album, remove_asset_from_album
    from immich_client.models.bulk_ids_dto import BulkIdsDto
    from immich_autotag.logging.utils import log
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.tags.modification_kind import ModificationKind
    from immich_autotag.config._internal_types import ErrorHandlingMode
    from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE

    moved_count = 0

    try:
        asset_ids = list(src.get_asset_ids() or [])
    except Exception:
        asset_ids = []

    for aid in asset_ids:
        try:
            aid_uuid = UUID(aid)
        except Exception:
            log(f"Skipping invalid asset id '{aid}' while merging albums.", level=LogLevel.WARNING)
            continue

        # Add to destination album
        try:
            add_result = add_assets_to_album.sync(id=UUID(dest.get_album_id()), client=client, body=BulkIdsDto(ids=[aid_uuid]))
            # Expect a list response with elements containing id and success
            if not isinstance(add_result, list):
                raise RuntimeError(f"add_assets_to_album returned unexpected type: {type(add_result)}")
            # Inspect result for this id
            success_add = None
            for item in add_result:
                try:
                    if item.id == str(aid):
                        success_add = bool(item.success)
                        break
                except Exception:
                    continue
            if success_add is not True:
                raise RuntimeError(f"Failed to add asset {aid} to album {dest.get_album_id()}: add_result={add_result}")
        except Exception as e:
            # Respect development mode
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise
            log(f"Warning: failed to add asset {aid} to dest album {dest.get_album_id()}: {e}", level=LogLevel.WARNING)
            # Continue to next asset
            continue

        # Remove from source album
        try:
            rem_result = remove_asset_from_album.sync(id=UUID(src.get_album_id()), client=client, body=BulkIdsDto(ids=[aid_uuid]))
            if not isinstance(rem_result, list):
                raise RuntimeError(f"remove_asset_from_album returned unexpected type: {type(rem_result)}")
            success_rem = None
            for item in rem_result:
                try:
                    if item.id == str(aid):
                        success_rem = bool(item.success)
                        break
                except Exception:
                    continue
            if success_rem is not True:
                raise RuntimeError(f"Failed to remove asset {aid} from album {src.get_album_id()}: rem_result={rem_result}")
        except Exception as e:
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise
            log(f"Warning: failed to remove asset {aid} from src album {src.get_album_id()}: {e}", level=LogLevel.WARNING)
            # We attempted to add to dest but could not remove from source; continue
            if tag_mod_report:
                tag_mod_report.add_assignment_modification(
                    kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                    asset_wrapper=None,
                    album=dest,
                    extra={"asset_id": aid, "note": "added_but_not_removed"},
                )
            moved_count += 1
            # Attempt to refresh caches
            try:
                dest.reload_from_api(client)
                src.reload_from_api(client)
            except Exception:
                pass
            continue

        # Success both add and remove
        moved_count += 1
        if tag_mod_report:
            # TagModification APIs expect asset_wrapper objects; if not available we log minimal info
            try:
                tag_mod_report.add_assignment_modification(
                    kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
                    asset_wrapper=None,
                    album=dest,
                    extra={"asset_id": aid},
                )
                tag_mod_report.add_assignment_modification(
                    kind=ModificationKind.REMOVE_ASSET_FROM_ALBUM,
                    asset_wrapper=None,
                    album=src,
                    extra={"asset_id": aid},
                )
            except Exception:
                pass

        # Refresh album caches incrementally
        try:
            dest.reload_from_api(client)
            src.reload_from_api(client)
        except Exception:
            # Non-fatal: continue
            pass

    return moved_count
