# Immich Proxy Refactor: Original to Destination Mapping

Esta tabla mapea los archivos y funciones actuales en `immich_autotag/api/immich_proxy/` a sus nombres de destino propuestos, buscando simetría con la estructura de entrypoints de la API.

| Original File/Folder      | Function Name                | Proposed Destination Name/Structure         | Hecho |
|--------------------------|------------------------------|--------------------------------------------|-------|
| albums.py                | proxy_get_album_info         | albums/get_album_info.py                   |       |
| albums.py                | proxy_remove_asset_from_album| albums/remove_asset_from_album.py          | ✅    |
| albums.py                | proxy_update_album_info      | albums/update_album_info.py                | ✅    |
| albums.py                | proxy_add_users_to_album     | albums/add_users_to_album.py               | ✅    |
| albums.py                | proxy_get_all_albums         | albums/get_all_albums.py                   | ✅    |
| albums.py                | proxy_get_album_page         | albums/get_album_page.py                   | ✅    |
| albums.py                | proxy_add_assets_to_album    | albums/add_assets_to_album.py              | ✅    |
| albums.py                | proxy_delete_album           | albums/delete_album.py                     | ✅    |
| assets.py                | proxy_get_asset_info         | assets/get_asset_info.py                   | ✅    |
| assets.py                | proxy_update_asset           | assets/update_asset.py                     | ✅    |
| client_types.py          | (alias/types)                | types/client_types.py                      |       |
| duplicates.py            | proxy_get_asset_duplicates   | duplicates/get_asset_duplicates.py         | ✅    |
| permissions.py           | proxy_search_users           | albums/search_users.py                     | ✅    |
| permissions.py           | proxy_remove_user_from_album | albums/remove_user_from_album.py           | ✅    |
| proxy_create_album.py    | proxy_create_album           | albums/create_album.py                     | ✅    |
| search.py                | proxy_search_assets          | search/search.py                           | ✅    |
| server.py                | proxy_get_server_statistics  | server/get_server_statistics.py            | ✅    |
| tags.py                  | proxy_tag_assets             | tags/tag_assets.py                         | ✅    |
| types.py                 | (all funciones)              | types/__init__.py                          | ✅    |
| users.py                 | (all funciones)              | users/get_user_info.py                     | ✅    |

## Notas
- Los nombres de destino buscan reflejar la estructura de entrypoints de la API.
- Todas las funciones y archivos principales ya han sido movidos y marcados como hechos.
- El resto se irá marcando conforme se muevan y se actualicen los imports.
- Al finalizar, se hará una revisión completa.

---

Actualiza esta tabla conforme avanza el refactor.