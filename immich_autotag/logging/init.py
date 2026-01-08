import logging

from typeguard import typechecked

from immich_autotag.config.experimental_config.manager import ExperimentalConfigManager
from immich_autotag.logging.levels import LogLevel
from immich_autotag.logging.utils import log, setup_logging


@typechecked
def initialize_logging() -> None:
    """
    Initializes the logging system depending on whether there is an asset filter or not.
    """
    # Silence HTTP logs from httpx and noisy dependencies
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    manager = ExperimentalConfigManager.get_instance()
    if manager.config is None:
        raise RuntimeError("ExperimentalConfigManager.config is not initialized!")
    filter_asset_links = manager.config.filter_out_asset_links
    if filter_asset_links is None:
        raise RuntimeError("filter_out_asset_links is not set in configuration!")
    if filter_asset_links and len(filter_asset_links) > 0:
        setup_logging(level=LogLevel.FOCUS)
        log(
            "[LOG] Logging system initialized: FOCUS level (filter mode)",
            level=LogLevel.FOCUS,
        )
    else:
        setup_logging(level=LogLevel.PROGRESS)
        log(
            "[LOG] Logging system initialized: PROGRESS level (normal mode)",
            level=LogLevel.PROGRESS,
        )
