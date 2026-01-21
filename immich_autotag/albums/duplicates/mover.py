"""Move assets between two albums (one-by-one).

Provides a single helper function that moves assets from a source album
wrapper into a destination album wrapper by adding each asset to the
destination and removing it from the source. The operation is performed
one asset at a time and records modifications in `ModificationReport` if
provided. Behavior respects `DEFAULT_ERROR_MODE` (fail-fast in
DEVELOPMENT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types import ImmichClient

if TYPE_CHECKING:
    from immich_autotag.albums.albums.album_collection_wrapper import (
        AlbumCollectionWrapper,
    )


@typechecked
def move_assets_between_albums(
    collection: "AlbumCollectionWrapper",
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
    from immich_autotag.config._internal_types import ErrorHandlingMode
    from immich_autotag.config.internal_config import DEFAULT_ERROR_MODE
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    moved_count = 0
    tag_mod_report = tag_mod_report or collection.get_modification_report()

    try:
        asset_wrappers = src.wrapped_assets(collection.context)
    except Exception:
        asset_wrappers = []

    for asset_wrapper in asset_wrappers:
        # Add to destination album using wrapper logic (handles duplicates)
        try:
            dest.add_asset(asset_wrapper, client, tag_mod_report)
        except Exception as e:
            from immich_autotag.albums.album.album_response_wrapper import (
                AssetAlreadyInAlbumError,
            )

            if isinstance(e, AssetAlreadyInAlbumError):
                # Asset already in album: treat as non-error, continue as normal
                pass
            elif DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise
            else:
                log(
                    f"Warning: failed to add asset {asset_wrapper.id} to dest album {dest.get_album_id()}: {e}",
                    level=LogLevel.WARNING,
                )
                continue

        # Remove from source album using wrapper logic
        try:
            src.remove_asset(asset_wrapper, client, tag_mod_report)
        except Exception as e:
            if DEFAULT_ERROR_MODE == ErrorHandlingMode.DEVELOPMENT:
                raise
            log(
                f"Warning: failed to remove asset {asset_wrapper.id} from src album {src.get_album_id()}: {e}",
                level=LogLevel.WARNING,
            )
            continue

        moved_count += 1
        # Optionally refresh album caches
        try:
            dest.reload_from_api(client)
            src.reload_from_api(client)
        except Exception:
            pass

    return moved_count
