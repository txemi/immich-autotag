"""
Re-export Immich types and DTOs for architectural compliance.
Only logging_proxy may import from immich_proxy.types.
"""
from immich_autotag.api.immich_proxy.types import (
    TagResponseDto,
    immich_errors,
    AlbumUserRole,
    AuthenticatedClient,
    ImmichClient,
    AssetResponseDto,
    UNSET,
    Unset,
    UpdateAssetDto,
    Client,
    MetadataSearchDto,
    Response,
)
