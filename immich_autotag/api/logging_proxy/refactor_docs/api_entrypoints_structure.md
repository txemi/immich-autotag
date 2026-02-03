# API Entrypoints Structure (Reference)

This document captures the folder and file structure of the Immich API client package, to guide the refactor and naming alignment for logging_proxy modules.

## Top-level API Folders
- activities/
- albums/
- api_keys/
- assets/
- authentication/
- authentication_admin/
- download/
- duplicates/
- faces/
- jobs/
- libraries/
- maintenance_admin/
- map_/
- memories/
- notifications/
- notifications_admin/
- partners/
- people/
- plugins/
- queues/
- search/
- server/
- sessions/
- shared_links/
- stacks/
- sync/
- system_config/
- system_metadata/
- tags/
- timeline/
- trash/
- users/
- users_admin/
- views/
- workflows/

## Example: tags/
- __init__.py
- bulk_tag_assets.py
- create_tag.py
- delete_tag.py
- get_all_tags.py
- get_tag_by_id.py
- tag_assets.py
- untag_assets.py
- update_tag.py
- upsert_tags.py

## Example: albums/
- __init__.py
- add_assets_to_album.py
- add_assets_to_albums.py
- add_users_to_album.py
- create_album.py
- delete_album.py
- get_album_info.py
- get_album_statistics.py
- get_all_albums.py
- remove_asset_from_album.py
- remove_user_from_album.py
- update_album_info.py
- update_album_user.py

## Example: assets/
- __init__.py
- check_bulk_upload.py
- check_existing_assets.py
- copy_asset.py
- delete_asset_metadata.py
- delete_assets.py
- download_asset.py
- get_all_user_assets_by_device_id.py
- get_asset_info.py
- get_asset_metadata.py
- get_asset_metadata_by_key.py
- get_asset_ocr.py
- get_asset_statistics.py
- get_random.py
- play_asset_video.py
- replace_asset.py
- run_asset_jobs.py
- update_asset.py
- update_asset_metadata.py
- update_assets.py
- upload_asset.py
- view_asset.py

---

This structure should be used as a reference for renaming and organizing logging_proxy modules, aiming for symmetry and clarity with the API client package.