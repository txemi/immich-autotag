"""
User Configuration Override Logic

This module encapsulates the logic for overriding user configuration values with internal settings or hardcoded filters. The goal is to centralize and simplify configuration management, so that the main application flow only needs to reference a single user configuration object, which has already been adjusted according to internal priorities and overrides.

Motivation:
- Currently, the application uses both a user configuration file and an internal config file (e.g., 'internal_config'), which can override user settings for development or special flows.
- This leads to complexity in the main application logic, which must check two sources and resolve conflicts.
- By centralizing override logic here, we ensure that the main flow only interacts with the user config, and all overrides are applied during config loading.

How it works:
- This module provides functions/classes to apply overrides to the user configuration object.
- Internal config values (such as asset processing limits) are detected and, if present, take precedence over user config values.
- Future additions (such as hardcoded filters) will also be applied here, so that the user config is always up-to-date and reflects all active overrides.

Usage:
- The main application should load user config as usual, then call the override logic from this module to apply any internal or hardcoded settings.
- After this, the user config object is the single source of truth for all configuration values.

This approach improves maintainability, clarity, and encapsulation, and makes it easier to add new override logic without complicating the main application flow.
"""

# Example stub for override logic

from immich_autotag.config.models import ClassificationRule, UserConfig


def add_asset_filter_override(user_config: UserConfig, asset_uuid: str) -> None:
    """
    Adds a ClassificationRule filter for the given asset_uuid to user_config.filters.filter_in.
    If user_config.filters is None, initializes it.
    """
    from immich_autotag.config.models import FilterConfig

    new_rule = ClassificationRule(asset_links=[asset_uuid])
    if user_config.filters is None:
        user_config.filters = FilterConfig(filter_in=[new_rule])
    else:
        user_config.filters.filter_in.append(new_rule)


def apply_config_overrides(user_config: UserConfig):
    """
    Apply internal overrides to user_config. If internal_config is provided and contains values
    that should take precedence, update user_config accordingly.
    This is a stub; actual logic will be added iteratively.
    """
    from immich_autotag.config.internal_config import (
        FILTER_OVERRIDE_ASSET_UUID,
        FORCE_FAIL_FAST_ON_ASSET_ERRORS,
    )

    if FILTER_OVERRIDE_ASSET_UUID is not None:
        add_asset_filter_override(user_config, FILTER_OVERRIDE_ASSET_UUID)

    if FORCE_FAIL_FAST_ON_ASSET_ERRORS is not None:
        user_config.performance.fail_fast_on_asset_errors = (
            FORCE_FAIL_FAST_ON_ASSET_ERRORS
        )

    # Add more overrides as needed
    return user_config
