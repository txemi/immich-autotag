# Immich Proxy Refactor: Original to Destination Mapping

This table maps the current files in `immich_autotag/api/immich_proxy/` to their proposed destination names, aiming for symmetry with the API entrypoints structure.

| Original File/Folder      | Proposed Destination Name/Structure         |
|--------------------------|--------------------------------------------|
| albums.py                | albums/get_album_info.py                   |
| assets.py                | assets/get_asset_info.py                   |
| client_types.py          | types/client_types.py                      |
| duplicates.py            | duplicates/get_asset_duplicates.py         |
| permissions.py           | albums/album_permissions.py                |
| proxy_create_album.py    | albums/create_album.py                     |
| search.py                | search/search.py                           |
| server.py                | server/get_server_statistics.py            |
| tags.py                  | tags/tag_assets.py                         |
| types.py                 | types/__init__.py                          |
| users.py                 | users/get_user_info.py                     |

## Notes
- The destination names are chosen to match the API entrypoints structure as closely as possible.
- This mapping is a draft and should be reviewed before applying changes.
- Subfolders are created for clarity and symmetry.
- Update this table as the refactor progresses.

---

Update this table as the refactor progresses.