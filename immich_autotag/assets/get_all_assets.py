from __future__ import annotations

from typing import Generator, Optional

from immich_client.api.assets import get_asset_info
from immich_client.api.search import search_assets
from immich_client.models import MetadataSearchDto
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.search_asset_response_dto import \
    SearchAssetResponseDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.context.immich_context import ImmichContext


@typechecked
def get_all_assets(
    context: "ImmichContext", max_assets: int | None = None, skip_n: int = 0
) -> Optional[Generator[AssetResponseWrapper, None, None]]:
    # NOTE: Python's typeguard doesn't support empty generators well, so we allow Optional in the return.
    # If there are no assets, the function may return None and not an empty generator.
    """
    Generator that produces AssetResponseWrapper one by one as they are obtained from the API.
    Skips the first `skip_n` assets efficiently (without fetching their full info).
    """
    page = 1
    count = 0
    skipped = 0
    while True:
        body = MetadataSearchDto(page=page)
        response = search_assets.sync_detailed(client=context.client, body=body)
        if response.status_code != 200:
            raise RuntimeError(f"Error: {response.status_code} - {response.content}")
        assets_page = response.parsed.assets.items
        if not assets_page:
            break  # No more assets, terminate the generator
        for asset in assets_page:
            if skip_n and skipped < skip_n:
                skipped += 1
                continue
            if max_assets is not None and count >= max_assets:
                break
            asset_full = get_asset_info.sync(id=asset.id, client=context.client)
            if asset_full is not None:
                yield AssetResponseWrapper(asset=asset_full, context=context)
                count += 1
            else:
                raise RuntimeError(
                    f"[ERROR] Could not load asset with id={asset.id}. get_asset_info returned None."
                )
        abs_pos = skipped + count
        response_assets = response.parsed.assets
        assert isinstance(response_assets, SearchAssetResponseDto)
        total_assets = response_assets.total
        msg = f"Page {page}: {len(assets_page)} assets (full info) | Processed so far: {count} (absolute: {abs_pos}"
        if total_assets:
            msg += f"/{total_assets}"
        msg += ")"
        print(msg)
        if max_assets is not None and count >= max_assets:
            break
        if not response_assets.next_page:
            break
        page += 1
    # Ensures it's always a generator: if there are no assets, simply terminates without returning None
