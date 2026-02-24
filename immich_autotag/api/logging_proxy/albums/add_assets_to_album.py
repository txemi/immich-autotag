





@typechecked
def logging_add_assets_to_album(
     *, asset_wrapper: "AssetResponseWrapper", client: ImmichClient, album_wrapper
) -> list[BulkIdResponseDto]:
    """Executes the API call to add an asset to the album."""
    from immich_autotag.api.immich_proxy.albums.add_assets_to_album import (
        proxy_add_assets_to_album,
    )

    result = proxy_add_assets_to_album(
        album_id=self.get_album_uuid(),
        client=client,
        asset_ids=[asset_wrapper.get_id()],
    )

    # 3. Handle result
    item = self._find_asset_result_in_response(result, asset_wrapper.get_id())
    if item:
        if not item.success:
            self._handle_add_asset_error(
                bulk_id_response_dto=item, asset_wrapper= asset_wrapper,  album_wrapper=album_wrapper
            )
    else:
        raise RuntimeError(
            f"Asset {asset_wrapper.get_id()} not found in add_assets_to_album response."
        )


    # 4. Reporting
    entry = self._report_addition_to_modification_report(
        asset_wrapper, modification_report
    )

    # 5. Consistency Verification
    self._verify_asset_in_album_with_retry(asset_wrapper, client, max_retries=3)

    return result    