"""
DEPRECATED: Use immich_autotag.api.immich_proxy.types instead.

This module is kept for backward compatibility.
All immich_client types are now centralized in the 'types' module.
"""

from immich_autotag.api.immich_proxy.types import AuthenticatedClient, ImmichClient

__all__ = ["ImmichClient", "AuthenticatedClient"]
