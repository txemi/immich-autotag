from __future__ import annotations

from immich_autotag.config.manager import ConfigManager
from immich_autotag.logging.init import initialize_logging


def init_config_and_logging() -> ConfigManager:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.user_help import print_welcome_links

    manager = ConfigManager.get_instance()
    log("Initializing ConfigManager...", level=LogLevel.INFO)
    config = manager.get_config_or_raise()

    log("ConfigManager initialized successfully", level=LogLevel.INFO)
    initialize_logging()
    from immich_autotag.statistics.statistics_manager import StatisticsManager

    StatisticsManager.get_instance().save()
    print_welcome_links(config)
    return manager
