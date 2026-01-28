from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Generator

from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.metadata_search_dto import MetadataSearchDto
from immich_client.models.search_response_dto import SearchResponseDto
from immich_client.types import Response
from typeguard import typechecked

from immich_autotag.api.immich_proxy.search import (
    SearchResponseDto,
    proxy_search_assets,
)
from immich_autotag.assets.asset_dto_state import AssetDtoType
from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper
from immich_autotag.logging.utils import log_debug

if TYPE_CHECKING:
    from immich_autotag.context.immich_context import ImmichContext


@typechecked
def _fetch_assets_page(
    context: "ImmichContext", page: int
) -> Response[SearchResponseDto]:

    from immich_autotag.logging.utils import log_debug

    body = MetadataSearchDto(page=page)
    log_debug(f"[BUG] Before search_assets.sync_detailed, page={page}")
    # Use ImmichClient type for client
    response = proxy_search_assets(
        client=context.get_client_wrapper().get_client(), body=body
    )
    log_debug(f"[BUG] After search_assets.sync_detailed, page={page}")
    return response


@typechecked
def _yield_assets_from_page(
    assets_page: list[AssetResponseDto],
    start_idx: int,
    context: "ImmichContext",
    max_assets: int | None,
    count: int,
) -> Generator["AssetResponseWrapper", None, None]:

    # Use top-level imports where possible to avoid redefinition warnings.
    yielded = 0
    # Import AssetManager here to avoid circular imports

    # Use the explicit context getter to obtain the asset_manager
    asset_manager = context.get_asset_manager()
    # AssetManager is always expected to be present; remove None check
    for idx, asset in enumerate(assets_page):
        if idx < start_idx:
            continue
        if max_assets is not None and max_assets >= 0 and count + yielded >= max_assets:
            break
        # asset is always AssetResponseDto
        log_debug(f"[INFO] Using AssetManager to get wrapper, asset_id={asset.id}")
        wrapper = asset_manager.get_wrapper_for_asset_dto(
            asset_dto=asset, dto_type=AssetDtoType.SEARCH, context=context
        )
        yield wrapper
        yielded += 1


@typechecked
def _log_page_progress(
    page: int,
    assets_page: list[AssetResponseDto],
    count: int,
    abs_pos: int,
    total_assets: int | None,
    log: Callable[[str], None],
) -> None:
    msg = f"[PROGRESS] Page {page}: {len(assets_page)} assets (full info) | Processed so far: {count} (absolute: {abs_pos}"
    if total_assets:
        msg += f"/{total_assets}"
    msg += ")"
    log(msg)


@typechecked
def get_all_assets(
    context: "ImmichContext", max_assets: int | None = None, skip_n: int = 0
) -> Generator[AssetResponseWrapper, None, None]:
    # Always return a generator, even if empty, to avoid None return type for type safety.
    """
    Generator that produces AssetResponseWrapper one by one as they are obtained from the API.
    Skips the first `skip_n` assets efficiently (without fetching their full info).
    """
    # The actual page size is determined by the backend. Initially we assume 100, but we detect it in the first response.
    page_size = None  # Local variable for page size
    page = 1
    skip_offset = 0
    count = 0
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log

    log("Starting get_all_assets generator...", level=LogLevel.PROGRESS)
    first_page = True
    skip_applied = False

    # If there are no assets, yield nothing (empty generator)
    # This ensures the function always returns a generator, never None.
    while True:
        response = _fetch_assets_page(context, page)
        # response is expected to be a SearchResponseDto
        # If using httpx or a custom Response, adapt as needed
        # If response is a custom Response object, get .parsed
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            response_obj = parsed
        else:
            response_obj = response
        # Now response_obj should be a SearchResponseDto
        # assets_page should be a list[AssetResponseDto]
        # assets_page should be a list[AssetResponseDto]
        # Explicitly cast assets_page to correct type
        raw_items = response_obj.assets.items  # type: ignore
        if not isinstance(raw_items, list):
            assets_page = []
        else:
            # Filter only AssetResponseDto objects
            assets_page = [item for item in raw_items if isinstance(item, AssetResponseDto)]  # type: ignore
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
            page_size = len(assets_page)  # type: ignore
            if skip_n:
                page = (skip_n // page_size) + 1
                skip_offset = skip_n % page_size
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
        response_assets = getattr(response.parsed, "assets", None)
        total_assets = response_assets.total if response_assets is not None else None
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
        if response_assets is None or not getattr(response_assets, "next_page", None):
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
