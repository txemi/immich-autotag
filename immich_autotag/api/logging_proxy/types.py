"""
Explicit re-export of Immich types and DTOs for architectural compliance.
Only logging_proxy may import from immich_proxy.types.
"""

from immich_autotag.api.immich_proxy.types import (
    Unset,
    UpdateAssetDto,
    AssetResponseDto,
    TagResponseDto,
    AlbumUserRole,
    AuthenticatedClient,
    ImmichClient,
    Client,
    UNSET,
    immich_errors,
    MetadataSearchDto,
    Response,
)

__all__ = [
    "Unset",
    "UpdateAssetDto",
    "AssetResponseDto",
    "TagResponseDto",
    "AlbumUserRole",
    "AuthenticatedClient",
    "ImmichClient",
    "Client",
    "UNSET",
    "immich_errors",
    "MetadataSearchDto",
    "Response",
]
