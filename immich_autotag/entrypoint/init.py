from immich_autotag.config.manager import ConfigManager
from immich_autotag.types import ImmichClient
from immich_autotag.context.immich_client_wrapper import ImmichClientWrapper

def init_config_and_logging() -> ConfigManager:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.utils.user_help import print_welcome_links
    manager = ConfigManager.get_instance()
    log("Initializing ConfigManager...", level=LogLevel.INFO)
    if manager.config is None:
        log(
            "FATAL: ConfigManager.config is None after initialization. This suggests the config file failed to load properly. Check ~/.config/immich_autotag/config.py or config.yaml",
            level=LogLevel.ERROR,
        )
        raise RuntimeError("ConfigManager.config is None after initialization")
    log("ConfigManager initialized successfully", level=LogLevel.INFO)
    from immich_autotag.logging.init import initialize_logging
    initialize_logging()
    from immich_autotag.statistics.statistics_manager import StatisticsManager
    StatisticsManager.get_instance().save()
    print_welcome_links(manager.config)
    return manager

def init_client(manager: ConfigManager) -> tuple[ImmichClient, ImmichClientWrapper]:
    from immich_autotag.config.host_config import get_immich_base_url
    api_key = manager.config.server.api_key
    client = ImmichClient(
        base_url=get_immich_base_url(),
        token=api_key,
        prefix="",
        auth_header_name="x-api-key",
        raise_on_unexpected_status=True,
    )
    client_wrapper = ImmichClientWrapper.create_default_instance(client)
    return client, client_wrapper
