"""
Re-export Immich asset functions and DTOs for architectural compliance.
Only logging_proxy may import from immich_proxy.assets.
"""
from immich_autotag.api.immich_proxy.assets import (
    AssetResponseDto,
    proxy_get_asset_info,
    proxy_update_asset,
)
