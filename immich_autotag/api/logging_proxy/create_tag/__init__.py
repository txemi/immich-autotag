"""
Logging proxy for creating tags.

This package provides functions to create tags with automatic event logging,
error handling, and modification reporting.
"""

from __future__ import annotations

from immich_autotag.api.logging_proxy.create_tag.logging_create_tag import (
    logging_create_tag,
)

__all__ = [
    "logging_create_tag",
]
