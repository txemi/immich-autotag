"""
Type definitions and aliases for immich-autotag.

This module centralizes client type configuration, making it easy to:
- Ensure all code uses authenticated clients
- Change client implementation in one place
- Document architectural decisions

All Immich endpoints require authentication, so we use AuthenticatedClient
as the canonical client type throughout the application.

IMPORTANT: When instantiating ImmichClient, always configure Immich-specific
authentication parameters:

    client = ImmichClient(
        base_url=...,
        token=api_key,
        prefix="",  # Immich uses x-api-key (no "Bearer" prefix)
        auth_header_name="x-api-key",  # Immich header name
        raise_on_unexpected_status=True,
    )

See docs/issues/0022-client-type-centralization/ for the history of this decision.
"""

from immich_client.client import AuthenticatedClient

# The canonical client type for immich-autotag
# All endpoints require authentication
ImmichClient = AuthenticatedClient
