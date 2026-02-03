"""
Central re-export module for all immich_client types and DTOs.
This module serves as the single point of entry for all external immich_client imports,
maintaining architectural isolation according to the import-linter contract:
"Only immich_proxy can access immich_client"
"""

# Client types
from immich_client import Client
from immich_client import errors as immich_errors
from immich_client.client import AuthenticatedClient
from immich_client.models.add_users_dto import AddUsersDto
from immich_client.models.album_response_dto import AlbumResponseDto
from immich_client.models.album_user_add_dto import AlbumUserAddDto
from immich_client.models.album_user_response_dto import AlbumUserResponseDto
from immich_client.models.album_user_role import AlbumUserRole
from immich_client.models.asset_response_dto import AssetResponseDto
from immich_client.models.bulk_id_response_dto import BulkIdResponseDto
from immich_client.models.create_album_dto import CreateAlbumDto
from immich_client.models.duplicate_response_dto import DuplicateResponseDto
from immich_client.models.metadata_search_dto import MetadataSearchDto
from immich_client.models.tag_response_dto import TagResponseDto
from immich_client.models.update_album_dto import UpdateAlbumDto
from immich_client.models.update_asset_dto import UpdateAssetDto
from immich_client.models.user_admin_response_dto import UserAdminResponseDto
from immich_client.models.user_response_dto import UserResponseDto
from immich_client.types import UNSET, Response, Unset

# Type aliases for backward compatibility
ImmichClient = AuthenticatedClient

__all__ = [
    # Client
    "Client",
    "AuthenticatedClient",
    "ImmichClient",
    # Errors
    "immich_errors",
    # DTOs
    "AddUsersDto",
    "AlbumResponseDto",
    "AlbumUserAddDto",
    "AlbumUserResponseDto",
    "AlbumUserRole",
    "AssetResponseDto",
    "BulkIdResponseDto",
    "CreateAlbumDto",
    "DuplicateResponseDto",
    "MetadataSearchDto",
    "TagResponseDto",
    "UpdateAlbumDto",
    "UpdateAssetDto",
    "UserAdminResponseDto",
    "UserResponseDto",
    # Types
    "Response",
    "UNSET",
    "Unset",
]
