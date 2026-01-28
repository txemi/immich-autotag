from __future__ import annotations

from immich_autotag.config.host_config import get_immich_base_url
from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper
from immich_autotag.logging.init import initialize_logging
from immich_autotag.types import ImmichClient


def init_config_and_logging() -> ConfigManager:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.user_help import print_welcome_links

    manager = ConfigManager.get_instance()
    log("Initializing ConfigManager...", level=LogLevel.INFO)
    manager.get_config_or_raise()

    log("ConfigManager initialized successfully", level=LogLevel.INFO)
    initialize_logging()
    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()
    print_welcome_links(manager.get_config_or_raise())
    return manager


def init_client(manager: ConfigManager) -> ImmichClientWrapper:
    api_key = manager.get_config_or_raise().server.api_key
    client = ImmichClient(
        base_url=get_immich_base_url(),
        token=api_key,
        prefix="",
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
    )
    from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

    client_wrapper = ImmichClientWrapper.create_default_instance(client)
    return client_wrapper
