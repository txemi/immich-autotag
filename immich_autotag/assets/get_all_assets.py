from __future__ import annotations

from typing import TYPE_CHECKING, Generator, Optional

from immich_client.api.search import search_assets
from immich_client.models import MetadataSearchDto
from immich_client.models.search_asset_response_dto import SearchAssetResponseDto
from typeguard import typechecked

from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.utils import log_debug

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@typechecked
def _fetch_assets_page(context: "ImmichContext", page: int) -> object:

    from immich_autotag.logging.utils import log_debug

    body = MetadataSearchDto(page=page)
    log_debug(f"[BUG] Before search_assets.sync_detailed, page={page}")
    response = search_assets.sync_detailed(client=context.client, body=body)
    log_debug(f"[BUG] After search_assets.sync_detailed, page={page}")
    return response


@typechecked
def _yield_assets_from_page(
    assets_page: list,
    start_idx: int,
    context: "ImmichContext",
    max_assets: int | None,
    count: int,
) -> Generator["AssetResponseWrapper", None, None]:

    # Use top-level imports where possible to avoid redefinition warnings.
    yielded = 0
    for idx, asset in enumerate(assets_page):
        if idx < start_idx:
            continue
        # Only enforce limit when max_assets is a non-negative integer (None or -1 means unlimited)
        if max_assets is not None and max_assets >= 0 and count + yielded >= max_assets:
            break
        # OPTIMIZATION: Use asset_partial from search_assets instead of immediately fetching full asset.
        # Full asset (with tags) will be lazy-loaded on first access to tags property.
        # This defers get_asset_info API calls until tags are actually needed.
        if asset is not None:
            log_debug(
                f"[BUG] Creating AssetResponseWrapper with asset_partial, asset_id={asset.id}"
            )
            yield AssetResponseWrapper(asset_partial=asset, context=context)
            yielded += 1
        else:
            log_debug(
                "[BUG] [ERROR] Could not load asset from search. search_assets returned None."
            )
            raise RuntimeError(
                "[ERROR] Could not load asset from search. search_assets returned None."
            )


@typechecked
def _log_page_progress(
    page: int,
    assets_page: list,
    count: int,
    abs_pos: int,
    total_assets: int | None,
    log: callable,
) -> None:
    msg = f"[PROGRESS] Page {page}: {len(assets_page)} assets (full info) | Processed so far: {count} (absolute: {abs_pos}"
    if total_assets:
        msg += f"/{total_assets}"
    msg += ")"
    log(msg)


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
    # The actual page size is determined by the backend. Initially we assume 100, but we detect it in the first response.
    PAGE_SIZE = None
    page = 1
    skip_offset = 0
    count = 0
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log("Starting get_all_assets generator...", level=LogLevel.PROGRESS)
    first_page = True
    skip_applied = False
    while True:
        response = _fetch_assets_page(context, page)
        if response.status_code != 200:
            log_debug(f"[BUG] Error: {response.status_code} - {response.content}")
            raise RuntimeError(f"Error: {response.status_code} - {response.content}")
        assets_page = response.parsed.assets.items
        log(
            f"[PROGRESS] Page {page}: {len(assets_page)} assets received from API.",
            level=LogLevel.PROGRESS,
        )
        if not assets_page:
            log(
                f"[PROGRESS] No more assets in page {page}, ending loop.",
                level=LogLevel.PROGRESS,
            )
            break
        if first_page:
            PAGE_SIZE = len(assets_page)
            if skip_n:
                page = (skip_n // PAGE_SIZE) + 1
                skip_offset = skip_n % PAGE_SIZE
            first_page = False
        # Apply skip only on the first page processed after calculation
        start_idx = skip_offset if skip_n and not skip_applied else 0
        log(
            f"[PROGRESS] skip_n={skip_n}, page={page}, skip_offset={skip_offset}, start_idx={start_idx}, count={count}",
            level=LogLevel.DEBUG,
        )
        log(
            f"[PROGRESS] Yielding from page {page} with start_idx={start_idx}, count={count}",
            level=LogLevel.DEBUG,
        )
        for asset_wrapper in _yield_assets_from_page(
            assets_page, start_idx, context, max_assets, count
        ):
            yield asset_wrapper
            count += 1
            log(f"[PROGRESS] Asset processed, count={count}", level=LogLevel.DEBUG)
        skip_applied = skip_n and not skip_applied
        abs_pos = skip_n + count
        response_assets = response.parsed.assets
        assert isinstance(response_assets, SearchAssetResponseDto)
        total_assets = response_assets.total
        _log_page_progress(
            page,
            assets_page,
            count,
            abs_pos,
            total_assets,
            lambda m: log(m, level=LogLevel.PROGRESS),
        )
        # Only enforce limit when max_assets is a non-negative integer (None or -1 means unlimited)
        if max_assets is not None and max_assets >= 0 and count >= max_assets:
            log(
                f"[PROGRESS] max_assets reached after processing page {page} (count={count})",
                level=LogLevel.PROGRESS,
            )
            break
        if not response_assets.next_page:
            log(
                f"[PROGRESS] No next_page in response after page {page}, ending loop.",
                level=LogLevel.PROGRESS,
            )
            break
        page += 1
    log(
        "get_all_assets generator finished (no more pages or assets).",
        level=LogLevel.PROGRESS,
    )
