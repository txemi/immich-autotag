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

from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.albums.albums.album_collection_wrapper import AlbumCollectionWrapper
from immich_autotag.report.modification_entries_list import ModificationEntriesList
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.client_types import ImmichClient


@typechecked
def move_assets_between_albums(
    *,
    collection: AlbumCollectionWrapper,
    dest: AlbumResponseWrapper,
    src: AlbumResponseWrapper,
    client: ImmichClient,
    tag_mod_report: Optional[ModificationReport] = None,
) -> ModificationEntriesList:
    """Move assets from `src` album into `dest` album one-by-one.

    Returns the number of assets successfully moved.

    Raises RuntimeError in DEVELOPMENT mode on unexpected API failures.
    In non-development modes failures are logged and the function attempts
    to continue.
    """
    # Local imports to avoid circular dependencies at module import time
    from immich_autotag.config.dev_mode import is_development_mode
    from immich_autotag.context.immich_context import ImmichContext
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.report.modification_entries_list import ModificationEntriesList

    tag_mod_report = tag_mod_report or collection.get_modification_report()

    ctx = ImmichContext.get_default_instance()
    asset_wrappers = src.wrapped_assets(ctx)
    modifications = ModificationEntriesList()
    for asset_wrapper in asset_wrappers:
        # Add to destination album using wrapper logic (handles duplicates)
        try:
            dest.add_asset(
                asset_wrapper=asset_wrapper,
                client=client,
                modification_report=tag_mod_report,
            )
        except Exception as e:
            from immich_autotag.albums.album.album_response_wrapper import (
                AssetAlreadyInAlbumError,
            )

            if isinstance(e, AssetAlreadyInAlbumError):
                # Asset already in album: treat as non-error, continue as normal
                pass
            elif is_development_mode():
                raise
            else:
                log(
                    f"Warning: failed to add asset {asset_wrapper.get_id()} to dest album {dest.get_album_uuid()}: {e}",
                    level=LogLevel.WARNING,
                )
                continue

        # Remove from source album using wrapper logic
        try:
            report_entry: ModificationEntry | None = src.remove_asset(
                asset_wrapper=asset_wrapper,
                client=client,
                modification_report=tag_mod_report,
            )
            if report_entry is not None:
                modifications.append(report_entry)

        except Exception as e:
            if is_development_mode():
                raise
            log(
                f"Warning: failed to remove asset {asset_wrapper.get_id()} from src album {src.get_album_uuid()}: {e}",
                level=LogLevel.WARNING,
            )
            continue

    return modifications
