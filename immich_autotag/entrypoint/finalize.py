from immich_autotag.config.manager import ConfigManager
from immich_autotag.types import ImmichClient

def finalize(manager: ConfigManager, client: ImmichClient) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper
    log("[OK] Main process completed successfully.", level=LogLevel.FOCUS)
    from immich_autotag.utils.user_help import print_welcome_links
    print_welcome_links(manager.config)
    deleted_count = TagCollectionWrapper.maintenance_delete_conflict_tags(client)
    if deleted_count > 0:
        log(
            f"[CLEANUP] Deleted {deleted_count} duplicate/conflict autotag labels.",
            level=LogLevel.INFO,
        )
