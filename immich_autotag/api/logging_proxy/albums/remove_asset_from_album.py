#


from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_kind import ModificationKind
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.utils.decorators import conditional_typechecked


@typechecked
def _execute_remove_asset_api(
    *,
    album: "AlbumResponseWrapper",
    asset_wrapper: "AssetResponseWrapper",
) -> list[BulkIdResponseDto]:
    """Executes the API call to remove an asset from the album."""
    from immich_autotag.api.immich_proxy.albums.remove_asset_from_album import (
        proxy_remove_asset_from_album,
    )
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client = ImmichClientWrapper.get_default_instance().get_client()
    result = proxy_remove_asset_from_album(
        album_id=album.get_album_uuid(),
        client=client,
        asset_ids=[asset_wrapper.get_id()],
    )
    if result is None:
        raise RuntimeError(
            f"Failed to remove asset {asset_wrapper.get_id()} from album {album.get_album_uuid()}: API returned None"
        )
    if len(result) != 1:
        raise RuntimeError(
            f"Failed to remove asset {asset_wrapper.get_id()} from album {album.get_album_uuid()}: API returned empty result list"
        )
    result1: BulkIdResponseDto = result[0]
    if result1.error:
        raise RuntimeError(
            f"Failed to remove asset {asset_wrapper.get_id()} from album {album.get_album_uuid()}: API error: {result1.error}"
        )
    if not result1.success:
        raise RuntimeError(
            f"Failed to remove asset {asset_wrapper.get_id()} from album {album.get_album_uuid()}: API returned success=False"
        )
    return result


def _handle_album_not_found_during_removal(
    *,
    album: "AlbumResponseWrapper",
    error_msg: str | None,
    asset_url: str,
    album_url: str,
) -> None:
    """Handles the case where the album is missing during an asset removal."""
    try:
        from immich_autotag.albums.albums.album_collection_wrapper import (
            AlbumCollectionWrapper,
        )

        collection = AlbumCollectionWrapper.get_instance()
        collection.remove_album_local(album)
        log(
            (
                f"[ALBUM REMOVAL] Album {album.get_album_uuid()} "
                f"('{album.get_album_name()}') removed from collection due to "
                f"not_found error during asset removal."
            ),
            level=LogLevel.FOCUS,
        )
    except Exception as e:
        log(
            (
                f"[ALBUM REMOVAL] Failed to remove album {album.get_album_uuid()} "
                f"from collection after not_found: {e}"
            ),
            level=LogLevel.WARNING,
        )

    log(
        (
            f"[ALBUM REMOVAL] Asset could not be removed because album "
            f"{album.get_album_uuid()} was not found (HTTP 404): {error_msg}\n"
            f"Asset link: {asset_url}\n"
            f"Album link: {album_url}"
        ),
        level=LogLevel.WARNING,
    )


def _handle_remove_asset_error(
    *,
    album: "AlbumResponseWrapper",
    item: BulkIdResponseDto,
    asset_wrapper: "AssetResponseWrapper",
) -> ModificationEntry:
    """Handles non-success results from removal API."""
    from immich_client.types import UNSET

    error_msg: str | None = None if item.error is UNSET else str(item.error)
    asset_url = asset_wrapper.get_immich_photo_url().geturl()
    album_url = album.get_immich_album_url().geturl()

    # Handle known recoverable errors
    if error_msg is not None and (
        str(error_msg).lower() in ("not_found", "no_permission")
    ):
        if str(error_msg).lower() == "not_found":
            _handle_album_not_found_during_removal(
                error_msg=error_msg,
                asset_url=asset_url,
                album_url=album_url,
                album=album,
            )
            # Asset not found in album - likely due to stale cache data
            # This is not a fatal error, just log as warning and continue
            log(
                (
                    f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} could not be removed from "
                    f"album {album.get_album_uuid()}: {error_msg}\n"
                    f"Asset link: {asset_url}\n"
                    f"Album link: {album_url}"
                ),
                level=LogLevel.WARNING,
            )
            # Register warning event in modification report

            # Return a ModificationEntry, not the report
            from immich_autotag.report.modification_report import ModificationReport

            tag_mod_report = ModificationReport.get_instance()
            return tag_mod_report.add_assignment_modification(
                kind=ModificationKind.WARNING_ASSET_NOT_IN_ALBUM,
                asset_wrapper=asset_wrapper,
                album=album,
                extra={"error": error_msg},
            )

    # Otherwise, treat as fatal
    raise RuntimeError(
        (
            f"Asset {asset_wrapper.get_id()} was not successfully removed from album "
            f"{album.get_album_uuid()}: {error_msg}\n"
            f"Asset link: {asset_url}\n"
            f"Album link: {album_url}"
        )
    )


@typechecked
def _handle_missing_remove_response(
    *, album: "AlbumResponseWrapper", asset_wrapper: "AssetResponseWrapper"
) -> None:
    """Handles the case where the asset is not found in the removal response."""
    log(
        (
            f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} not found in "
            f"remove_assets_from_album response for album "
            f"{album.get_album_uuid()}. Treating as already removed."
        ),
        level=LogLevel.WARNING,
    )
    from immich_autotag.config.dev_mode import is_development_mode

    if is_development_mode():
        raise RuntimeError(
            f"Asset {asset_wrapper.get_id()} not found in removal response for album "
            f"{album.get_album_uuid()}."
        )


@typechecked
def _report_removal_to_modification_report(
    *,
    album: "AlbumResponseWrapper",
    asset_wrapper: "AssetResponseWrapper",
    tag_mod_report: "ModificationReport",
) -> ModificationEntry:
    """Records the asset removal in the modification report."""
    from immich_autotag.report.modification_kind import ModificationKind

    return tag_mod_report.add_assignment_modification(
        kind=ModificationKind.REMOVE_ASSET_FROM_ALBUM,
        asset_wrapper=asset_wrapper,
        album=album,
    )


@conditional_typechecked
def _verify_asset_removed_from_album_with_retry(
    *,
    album: "AlbumResponseWrapper",
    asset_wrapper: "AssetResponseWrapper",
    max_retries: int = 3,
) -> None:
    """
    Verifies that an asset has been removed from the album after removing it,
    with retry logic for eventual consistency.
    Uses exponential backoff to handle API delays.
    """
    import time

    for attempt in range(max_retries):
        if not album.has_asset_wrapper(asset_wrapper):
            return  # Success - asset is no longer in album

        if attempt < max_retries - 1:
            # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
            wait_time = 0.1 * (2**attempt)
            time.sleep(wait_time)
        else:
            log(
                (
                    f"After {max_retries} retries, asset {asset_wrapper.get_id()} "
                    f"still appears in album {album.get_album_uuid()}. "
                    f"This may be an eventual consistency or API issue."
                ),
                level=LogLevel.WARNING,
            )


@conditional_typechecked
def logging_remove_asset_from_album(
    *,
    album: "AlbumResponseWrapper",
    asset_wrapper: "AssetResponseWrapper",
) -> ModificationEntry | None:
    """
    Removes the asset from the album using the API and validates the result.

    Safe to call even if asset is not in album (idempotent operation).
    Raises exception only if the removal fails unexpectedly.
    """

    # 2. Execution
    result = _execute_remove_asset_api(album=album, asset_wrapper=asset_wrapper)

    # 3. Handle result
    from immich_autotag.api.logging_proxy.albums.add_assets_to_album import (
        _find_asset_result_in_response,
    )

    item = _find_asset_result_in_response(result, asset_wrapper.get_id())
    if item:
        if not item.success:
            removal_entry = _handle_remove_asset_error(
                album=album,
                item=item,
                asset_wrapper=asset_wrapper,
            )
            return removal_entry
    else:
        _handle_missing_remove_response(album=album, asset_wrapper=asset_wrapper)
        return None

    # 4. Success Log
    log(
        (
            f"[ALBUM REMOVAL] Asset {asset_wrapper.get_id()} removed from album "
            f"{album.get_album_uuid()} ('{album.get_album_name()}')."
        ),
        level=LogLevel.FOCUS,
    )

    # 5. Reporting
    from immich_autotag.report.modification_report import ModificationReport

    tag_mod_report = ModificationReport.get_instance()
    report_mod_entry: ModificationEntry = _report_removal_to_modification_report(
        album=album, asset_wrapper=asset_wrapper, tag_mod_report=tag_mod_report
    )

    # 6. Consistency Verification
    _verify_asset_removed_from_album_with_retry(
        asset_wrapper=asset_wrapper, max_retries=3, album=album
    )
    return report_mod_entry
