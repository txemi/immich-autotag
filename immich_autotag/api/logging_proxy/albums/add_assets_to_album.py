from immich_client.errors import UnexpectedStatus
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_dto_state import AlbumDtoState, AlbumLoadSource
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.api.immich_proxy.types import ImmichClient
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.errors.recoverable_error import (
    AlbumNotFoundError,
    PermissionDeniedError,
)
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.uuid_wrappers import AlbumUUID, AssetUUID
from immich_autotag.utils.decorators import conditional_typechecked


@conditional_typechecked
def _verify_asset_in_album_with_retry(
    *,
    asset_wrapper: "AssetResponseWrapper",
    album_id: AlbumUUID,
    client: ImmichClient,
    max_retries: int = 3,
) -> None:
    """
    Verifies that an asset appears in the album after adding it,
    with retry logic for eventual consistency.
    Uses exponential backoff to handle API delays.
    """
    import time

    from immich_autotag.api.immich_proxy.albums.get_album_info import (
        proxy_get_album_info,
    )

    for attempt in range(max_retries):
        album_info = proxy_get_album_info(
            album_id=album_id, client=client, use_cache=False
        )
        if album_info is not None:  # Validate album ID format
            album_wrapper = AlbumDtoState.from_album_info(
                album_info, load_source=AlbumLoadSource.DETAIL
            )
            if asset_wrapper.get_id() in album_wrapper.get_asset_uuids():
                return  # Success - asset is in album

        if attempt < max_retries - 1:
            # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
            wait_time = 0.1 * (2**attempt)
            time.sleep(wait_time)
        else:
            log(
                (
                    f"After {max_retries} retries, asset {asset_wrapper.get_id()} "
                    f"does NOT appear in album {album_id}. "
                    f"This may be an eventual consistency or "
                    f"API issue."
                ),
                level=LogLevel.WARNING,
            )


@typechecked
def _report_addition_to_modification_report(
    *, asset_wrapper: "AssetResponseWrapper", album_wrapper: AlbumResponseWrapper
) -> "ModificationEntry":
    """Records the asset addition in the modification report."""
    from immich_autotag.report.modification_kind import ModificationKind

    tag_mod_report = ModificationReport.get_instance()

    return tag_mod_report.add_assignment_modification(
        kind=ModificationKind.ASSIGN_ASSET_TO_ALBUM,
        asset_wrapper=asset_wrapper,
        album=album_wrapper,
    )


def _handle_add_asset_error(
    *,
    bulk_id_response_dto: BulkIdResponseDto,
    asset_wrapper: "AssetResponseWrapper",
    album_wrapper: AlbumResponseWrapper,
    album_state: AlbumDtoState,
    raise_on_duplicate: bool = True,
) -> ModificationEntry | None:
    """Handles non-success results from addition API.

    Args:
        raise_on_duplicate: If True, raises AssetAlreadyInAlbumError on duplicate.
                           If False, logs warning and returns ModificationEntry.
    """
    error_msg = bulk_id_response_dto.error
    asset_url = asset_wrapper.get_immich_photo_url().geturl()
    album_url = album_wrapper.get_immich_album_url().geturl()

    # If the error is 'duplicate', reactive refresh:
    # reload album data from API.
    if error_msg and "duplicate" in str(error_msg).lower():
        log(
            (
                f"Asset {asset_wrapper.get_id()} already in album "
                f"{album_wrapper.get_album_uuid()} (API duplicate error). "
                f"Raising AssetAlreadyInAlbumError."
            ),
            level=LogLevel.FOCUS,
        )
        # Instead of self.reload_from_api, use _cache_entry.ensure_full_loaded if available
        # AlbumCacheEntry._ensure_full_loaded is protected; use get_asset_uuids to force reload
        album_state.get_asset_uuids()

        from immich_autotag.report.modification_kind import ModificationKind
        from immich_autotag.report.modification_report import ModificationReport

        tag_mod_report = ModificationReport.get_instance()
        entry = tag_mod_report.add_assignment_modification(
            kind=ModificationKind.WARNING_ASSET_ALREADY_IN_ALBUM,
            asset_wrapper=asset_wrapper,
            album=album_wrapper,
            extra={
                "error": error_msg,
                "asset_url": asset_url,
                "album_url": album_url,
                "reason": "Stale cached album data detected and reloaded",
                "details": (
                    f"Asset {asset_wrapper.get_id()} was not successfully added to album "
                    f"{album_state.get_album_uuid()}: {error_msg}\n"
                    f"Asset link: {asset_url}\n"
                    f"Album link: {album_url}"
                ),
            },
        )

        if raise_on_duplicate:
            from immich_autotag.albums.album.album_response_wrapper import (
                AssetAlreadyInAlbumError,
            )

            raise AssetAlreadyInAlbumError(
                f"Asset {asset_wrapper.get_id()} already in album {album_state.get_album_uuid()} (API duplicate error)\n"
                f"Asset link: {asset_wrapper.get_link().geturl()}\n"
                f"Album link: {album_state.get_immich_album_url()}"
            )
        else:
            log(
                (
                    f"[WARNING] Asset {asset_wrapper.get_id()} already in album "
                    f"{album_state.get_album_uuid()} (API duplicate error). Continuing execution.\n"
                    f"Asset link: {asset_wrapper.get_link().geturl()}\n"
                    f"Album link: {album_state.get_immich_album_url()}"
                ),
                level=LogLevel.WARNING,
            )
        return entry
    else:
        raise RuntimeError(
            (
                f"Asset {asset_wrapper.get_id()} was not successfully added to album "
                f"{album_state.get_album_uuid()}: {error_msg}\n"
                f"Asset link: {asset_url}\n"
                f"Album link: {album_url}"
            )
        )


@typechecked
def _find_asset_result_in_response(
    result: list[BulkIdResponseDto], asset_id: AssetUUID
) -> BulkIdResponseDto | None:
    """Finds the result item for a specific asset in the API response list."""

    for item in result:
        # Validate that success is a boolean (can be True or False)
        if not isinstance(item.success, bool):
            raise RuntimeError(
                f"API returned non-boolean success value in BulkIdResponseDto: {type(item.success)} = {item.success}"
            )
        if AssetUUID.from_uuid_string(item.id) == asset_id:
            return item

    return None


@typechecked
def logging_add_assets_to_album(
    *,
    asset_wrapper: "AssetResponseWrapper",
    client: ImmichClient,
    album_wrapper: AlbumResponseWrapper,
    album_state: AlbumDtoState,
    raise_on_duplicate: bool = True,
) -> ModificationEntry | None:
    """Executes the API call to add an asset to the album.

    Args:
        raise_on_duplicate: If True, raises AssetAlreadyInAlbumError when asset is already in album.
                           If False, logs warning and continues execution, returning None.

    Returns:
        ModificationEntry if successful or None if asset already in album and raise_on_duplicate=False.

    Raises:
        AlbumNotFoundError: If album is deleted/not found (400 or 404 from API).
        PermissionDeniedError: If access is denied (403 from API).
    """
    from immich_autotag.api.immich_proxy.albums.add_assets_to_album import (
        proxy_add_assets_to_album,
    )

    album_url = album_wrapper.get_immich_album_url()
    asset_url = asset_wrapper.get_immich_photo_url()

    try:
        result = proxy_add_assets_to_album(
            album_id=album_wrapper.get_album_uuid(),
            client=client,
            asset_ids=[asset_wrapper.get_id()],
        )
    except UnexpectedStatus as e:
        # Capture API errors with enriched context (album + asset URLs)
        status_code = e.status_code
        response_content = (
            e.content.decode("utf-8")
            if isinstance(e.content, bytes)
            else str(e.content)
        )

        if status_code in (400, 404):
            # Album not found or deleted
            raise AlbumNotFoundError(
                message="Album not found or deleted during asset addition",
                status_code=status_code,
                response_content=response_content,
                album_url=album_url,
                asset_url=asset_url,
            ) from e
        elif status_code == 403:
            # Permission denied
            raise PermissionDeniedError(
                message="Permission denied when adding asset to album",
                status_code=status_code,
                response_content=response_content,
                album_url=album_url,
                asset_url=asset_url,
            ) from e
        else:
            # Other API errors - re-raise as generic RuntimeError with context
            raise RuntimeError(
                f"API error when adding asset {asset_wrapper.get_id()} to album {album_wrapper.get_album_uuid()}\n"
                f"Status: {status_code}\n"
                f"Response: {response_content}\n"
                f"Asset URL: {asset_url.geturl()}\n"
                f"Album URL: {album_url.geturl()}"
            ) from e

    # 3. Handle result
    item = _find_asset_result_in_response(result, asset_wrapper.get_id())
    if item:
        if not item.success:
            error_entry = _handle_add_asset_error(
                bulk_id_response_dto=item,
                asset_wrapper=asset_wrapper,
                album_wrapper=album_wrapper,
                album_state=album_state,
                raise_on_duplicate=raise_on_duplicate,
            )
            # If we didn't raise (raise_on_duplicate=False), return the error entry
            if error_entry is not None:
                return error_entry
    else:
        raise RuntimeError(
            f"Asset {asset_wrapper.get_id()} not found in add_assets_to_album response."
        )

    # 4. Reporting
    entry = _report_addition_to_modification_report(
        asset_wrapper=asset_wrapper, album_wrapper=album_wrapper
    )

    return entry
