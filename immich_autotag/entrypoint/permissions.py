from immich_autotag.config.manager import ConfigManager
from immich_autotag.context.immich_context import ImmichContext
from immich_autotag.permissions import process_album_permissions
from immich_autotag.albums.permissions.sync_all_album_permissions import sync_all_album_permissions

def process_permissions(manager: ConfigManager, context: ImmichContext) -> None:
    process_album_permissions(manager.config, context)
    sync_all_album_permissions(manager.config, context)
