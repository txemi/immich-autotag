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

from immich_autotag.logging.utils import log_debug
from typing import TYPE_CHECKING
if TYPE_CHECKING:
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
        log_debug(f"[BUG] Antes de search_assets.sync_detailed, page={page}")
        body = MetadataSearchDto(page=page)
        response = search_assets.sync_detailed(client=context.client, body=body)
        log_debug(f"[BUG] Después de search_assets.sync_detailed, page={page}")
        if response.status_code != 200:
            log_debug(f"[BUG] Error: {response.status_code} - {response.content}")
            raise RuntimeError(f"Error: {response.status_code} - {response.content}")
        assets_page = response.parsed.assets.items
        log_debug(f"[BUG] Página {page}: {len(assets_page)} assets recibidos de la API.")
        if not assets_page:
            log_debug(f"[BUG] No hay más assets en la página {page}, fin del bucle.")
            break  # No more assets, terminate the generator
        for asset in assets_page:
            if skip_n and skipped < skip_n:
                skipped += 1
                continue
            if max_assets is not None and count >= max_assets:
                log_debug(f"[BUG] max_assets alcanzado en la página {page} (count={count})")
                break
            log_debug(f"[BUG] Antes de get_asset_info.sync, asset_id={asset.id}")
            asset_full = get_asset_info.sync(id=asset.id, client=context.client)
            log_debug(f"[BUG] Después de get_asset_info.sync, asset_id={asset.id}")
            if asset_full is not None:
                log_debug(f"[BUG] Asset completo cargado: {asset.id}")
                yield AssetResponseWrapper(asset=asset_full, context=context)
                count += 1
            else:
                log_debug(f"[BUG] [ERROR] Could not load asset with id={asset.id}. get_asset_info returned None.")
                raise RuntimeError(
                    f"[ERROR] Could not load asset with id={asset.id}. get_asset_info returned None."
                )
        abs_pos = skipped + count
        response_assets = response.parsed.assets
        assert isinstance(response_assets, SearchAssetResponseDto)
        total_assets = response_assets.total
        msg = f"[BUG] Page {page}: {len(assets_page)} assets (full info) | Processed so far: {count} (absolute: {abs_pos}"
        if total_assets:
            msg += f"/{total_assets}"
        msg += ")"
        log_debug(msg)
        if max_assets is not None and count >= max_assets:
            log_debug(f"[BUG] max_assets alcanzado tras procesar página {page} (count={count})")
            break
        if not response_assets.next_page:
            log_debug(f"[BUG] No hay next_page en la respuesta tras página {page}, fin del bucle.")
            break
        page += 1
    log_debug("[BUG] El generador get_all_assets ha terminado (no quedan más páginas ni assets).")
