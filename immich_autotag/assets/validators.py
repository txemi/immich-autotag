"""
Validador de tipo para AssetResponseWrapper.
"""

from typing import Any

import attr


def validate_asset_response_wrapper(
    instance: Any, attribute: attr.Attribute[Any], value: Any
) -> None:
    """
    Permite None o AssetResponseWrapper.
    """
    if value is not None:
        from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

        if not isinstance(value, AssetResponseWrapper):
            raise TypeError(
                f"{attribute.name} must be AssetResponseWrapper or None, got {type(value)}"
            )


def validate_asset_response_wrapper_not_none(instance, attribute, value):
    """
    No permite None, solo AssetResponseWrapper.
    """
    from immich_autotag.assets.asset_response_wrapper import AssetResponseWrapper

    if value is None or not isinstance(value, AssetResponseWrapper):
        raise TypeError(
            f"{attribute.name} must be AssetResponseWrapper (not None), got {type(value)}"
        )
