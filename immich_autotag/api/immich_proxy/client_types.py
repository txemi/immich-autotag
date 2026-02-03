"""
DEPRECATED: Use immich_autotag.api.immich_proxy.types instead.
This module is kept for backward compatibility.
All immich_client types are now centralized in the 'types' module.
"""

from immich_client.client import AuthenticatedClient
from immich_client.client import AuthenticatedClient as ImmichClient

__all__ = ["ImmichClient", "AuthenticatedClient"]
