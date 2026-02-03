# Immich Proxy Refactor: Original to Destination Mapping

This table maps the current files and functions in `immich_autotag/api/immich_proxy/` to their proposed destination names, aiming for symmetry with the API entrypoints structure.

| Original File/Folder      | Function Name                | Proposed Destination Name/Structure         | Done |
|--------------------------|------------------------------|--------------------------------------------|------|
| albums.py                | proxy_get_album_info         | albums/get_album_info.py                   |      |
| albums.py                | proxy_remove_asset_from_album| albums/remove_asset_from_album.py          | ✅   |
| albums.py                | proxy_update_album_info      | albums/update_album_info.py                |      |
| albums.py                | proxy_add_users_to_album     | albums/add_users_to_album.py               |      |
| albums.py                | proxy_get_all_albums         | albums/get_all_albums.py                   |      |
| albums.py                | proxy_get_album_page         | albums/get_album_page.py                   |      |
| albums.py                | proxy_add_assets_to_album    | albums/add_assets_to_album.py              |      |
| albums.py                | proxy_delete_album           | albums/delete_album.py                     |      |
| assets.py                | (all functions)              | assets/get_asset_info.py                   |      |
| client_types.py          | (all functions)              | types/client_types.py                      |      |
| duplicates.py            | (all functions)              | duplicates/get_asset_duplicates.py         |      |
| permissions.py           | (all functions)              | albums/album_permissions.py                |      |
| proxy_create_album.py    | (all functions)              | albums/create_album.py                     |      |
| search.py                | (all functions)              | search/search.py                           |      |
| server.py                | (all functions)              | server/get_server_statistics.py            |      |
| tags.py                  | (all functions)              | tags/tag_assets.py                         |      |
| types.py                 | (all functions)              | types/__init__.py                          |      |
| users.py                 | (all functions)              | users/get_user_info.py                     |      |

## Notes
- The destination names are chosen to match the API entrypoints structure as closely as possible.
- Functions in albums.py are split into individual files for clarity and maintainability.
- This mapping is a draft and should be reviewed before applying changes.
- Update this table as the refactor progresses.

---

Update this table as the refactor progresses.