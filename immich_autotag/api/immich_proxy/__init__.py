"""
Immich API Proxy Layer

This package serves as the **single point of entry** for all interactions with the Immich API.

## Purpose

The immich_proxy layer provides controlled access to the external immich_client library,
ensuring:
- Centralized API interaction point
- Consistent error handling and logging
- Architectural isolation from the rest of the application
- Single responsibility: delegating to the real Immich API

## Key Principle

**All access to immich_client must flow through this proxy.**

No other module in immich-autotag should import directly from immich_client.
All API interactions should use the proxy modules provided here.

## Architecture

### Types & Client
- `types.py` - Central re-export of all immich_client types and DTOs
- `client_types.py` - DEPRECATED, use types.py instead

### API Proxies
Each proxy module handles a specific domain:
- `users.py` - User management endpoints
- `assets.py` - Asset/photo management endpoints
- `search.py` - Search functionality endpoints
- `tags.py` - Tag management endpoints
- `albums.py` - Album management endpoints
- `logging_proxy/` - Logging-only access layer

## Access Control Contracts

**Enforced Rules (TARGET level and higher):**

1. **Only logging_proxy can access immich_proxy internals** ← NEW
   - Only `immich_autotag.api.logging_proxy` should import proxy modules
   - (users.py, assets.py, search.py, tags.py, albums.py)
   - Other modules must use types or go through logging_proxy

2. **All immich_client imports flow through immich_proxy**
   - Only this package should import `immich_client` directly
   - All other modules import from `immich_autotag.api.immich_proxy.types`

## Example Usage

### ❌ WRONG - Direct import from immich_client
```python
from immich_client.models.asset_response_dto import AssetResponseDto
```

### ✅ CORRECT - Through proxy types
```python
from immich_autotag.api.logging_proxy.types import AssetResponseDto
```

### ✅ CORRECT - Through proxy functions
```python
from immich_autotag.api.logging_proxy.assets import get_all_assets
```

## Future Improvements

- Add request/response transformation layer for consistency
- Implement retry logic and circuit breakers
- Add comprehensive error mapping for Immich-specific errors
- Standardize pagination across all proxy modules
"""

__all__ = [
    "types",
    "client_types",
    "users",
    "assets",
    "search",
    "tags",
    "albums",
    "logging_proxy",
]
