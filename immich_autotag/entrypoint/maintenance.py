from __future__ import annotations

from immich_autotag.types import ImmichClient


def maintenance_cleanup_labels(client: ImmichClient) -> None:
    from immich_autotag.logging.levels import LogLevel
    from immich_autotag.logging.utils import log
    from immich_autotag.tags.tag_collection_wrapper import TagCollectionWrapper

    deleted_count = TagCollectionWrapper.maintenance_delete_conflict_tags(client)
    if deleted_count > 0:
        log(
            f"[CLEANUP] Deleted {deleted_count} duplicate/conflict autotag labels.",
            level=LogLevel.INFO,
        )
