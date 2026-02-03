# Logging Proxy Refactor: Original to Destination Mapping

This table maps the current files in `immich_autotag/api/logging_proxy/` to their proposed destination names, aiming for symmetry with the API entrypoints structure.

| Original File/Folder                | Proposed Destination Name/Structure         | Done |
|-------------------------------------|--------------------------------------------|------|
| add_members.py                      | albums/add_users_to_album.py               | ✅   |
| add_tags.py                         | tags/tag_assets.py                         | ✅   |
| assets.py                           | assets/get_asset_info.py                   | ✅   |
| create_tag/                         | tags/create_tag.py                         | ✅   |
| duplicates.py                       | duplicates/get_asset_duplicates.py         | ✅   |
| fetch_total_assets.py               | server/get_server_statistics.py            | ✅   |
| logging_delete_tag.py               | tags/delete_tag.py                         | ✅   |
| logging_untag_assets.py             | tags/untag_assets.py                       | ✅   |
| logging_update_asset_date.py        | assets/update_asset.py                     | ✅   |
| permissions.py                      | albums/album_permissions.py                | ✅   |
| remove_members.py                   | albums/remove_user_from_album.py           | ✅   |
| remove_tags.py                      | tags/remove_tags.py (deprecated)           | ✅   |
| tags.py                             | tags/__init__.py                           |
| types.py                            | types/__init__.py                          |

## Notes
- The destination names are chosen to match the API entrypoints structure as closely as possible.
- Deprecated files are marked and may be removed or merged as appropriate.
- Subfolders (e.g., `create_tag/`) are flattened where possible for clarity.
- This mapping is a draft and should be reviewed before applying changes.

---

Update this table as the refactor progresses.