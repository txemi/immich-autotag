"""
Explicit re-export of Immich asset functions and DTOs for architectural compliance.
Only logging_proxy may import from immich_proxy.assets.
"""

from immich_autotag.api.immich_proxy.assets import (
    AssetResponseDto,
    proxy_get_asset_info,
)

__all__ = [
    "AssetResponseDto",
    "proxy_get_asset_info",
]
