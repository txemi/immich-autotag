"""
Client type definitions for Immich API proxy layer.

This module is the ONLY place in immich-autotag that directly imports from immich_client.
All other modules must import client types through immich_autotag.types.client_types,
which re-exports from here.

This ensures architectural isolation: only immich_proxy has direct access to immich_client.
"""

from immich_client.client import AuthenticatedClient

# The canonical client type for immich-autotag
# All endpoints require authentication
ImmichClient = AuthenticatedClient

__all__ = ["ImmichClient", "AuthenticatedClient"]
