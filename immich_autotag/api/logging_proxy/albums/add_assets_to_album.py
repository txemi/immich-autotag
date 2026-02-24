from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from typeguard import typechecked

from immich_autotag.albums.album.album_dto_state import AlbumDtoState
from immich_autotag.albums.album.album_response_wrapper import AlbumResponseWrapper
from immich_autotag.api.immich_proxy.types import ImmichClient
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log
from immich_autotag.report.modification_entry import ModificationEntry
from immich_autotag.report.modification_report import ModificationReport
from immich_autotag.types.uuid_wrappers import AssetUUID
from immich_autotag.utils.decorators import conditional_typechecked

@conditional_typechecked
def _verify_asset_in_album_with_retry(*,
    asset_wrapper: "AssetResponseWrapper",
    client: ImmichClient,
    max_retries: int = 3,
) -> None:
    """
    Verifies that an asset appears in the album after adding it,
    with retry logic for eventual consistency.
    Uses exponential backoff to handle API delays.
    """
    import time

    for attempt in range(max_retries):
        if self._cache_entry.has_asset_wrapper(asset_wrapper):
            return  # Success - asset is in album

        if attempt < max_retries - 1:
            # Exponential backoff: 0.1s, 0.2s, 0.4s, etc.
            wait_time = 0.1 * (2**attempt)
            time.sleep(wait_time)
        else:
            log(
                (
                    f"After {max_retries} retries, asset {asset_wrapper.get_id()} "
                    f"does NOT appear in album {self.get_album_uuid()}. "
                    f"This may be an eventual consistency or "
                    f"API issue."
                ),
                level=LogLevel.WARNING,
            )

@typechecked
def _report_addition_to_modification_report(*,
    asset_wrapper: "AssetResponseWrapper",album_wrapper: AlbumResponseWrapper
) -> "ModificationEntry":
    """Records the asset addition in the modification report."""
    from immich_autotag.report.modification_kind import ModificationKind
    from immich_autotag.report.modification_report import ModificationReport
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
    album_state: AlbumDtoState
) -> None:
    """Handles non-success results from addition API."""
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
        tag_mod_report.add_assignment_modification(
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
        from immich_autotag.albums.album.album_response_wrapper import (
            AssetAlreadyInAlbumError,
        )

        raise AssetAlreadyInAlbumError(
            f"Asset {asset_wrapper.get_id()} already in album {album_state.get_album_uuid()} (API duplicate error)\n"
            f"Asset link: {asset_wrapper.get_link().geturl()}\n"
            f"Album link: {album_state.get_immich_album_url().geturl()}"
        )
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
    result: list[BulkIdResponseDto], asset_id: "AssetUUID"
) -> BulkIdResponseDto | None:
    """Finds the result item for a specific asset in the API response list."""
    from immich_autotag.types.uuid_wrappers import AssetUUID

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
    *, asset_wrapper: "AssetResponseWrapper", client: ImmichClient, album_wrapper: AlbumResponseWrapper, album_state: AlbumDtoState, 
) -> list[BulkIdResponseDto]:
    """Executes the API call to add an asset to the album."""
    from immich_autotag.api.immich_proxy.albums.add_assets_to_album import (
        proxy_add_assets_to_album,
    )

    result = proxy_add_assets_to_album(
        album_id=album_wrapper.get_album_uuid(),
        client=client,
        asset_ids=[asset_wrapper.get_id()],
    )

    # 3. Handle result
    item = _find_asset_result_in_response(result, asset_wrapper.get_id())
    if item:
        if not item.success:
            _handle_add_asset_error(
                bulk_id_response_dto=item,
                asset_wrapper=asset_wrapper,
                album_wrapper=album_wrapper,album_state=album_state
            )
    else:
        raise RuntimeError(
            f"Asset {asset_wrapper.get_id()} not found in add_assets_to_album response."
        )

    # 4. Reporting
    entry = _report_addition_to_modification_report(asset_wrapper=asset_wrapper,album_wrapper=album_wrapper)

    # 5. Consistency Verification
    self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

    return result
