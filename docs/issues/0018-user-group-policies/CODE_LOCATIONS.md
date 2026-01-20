
# Location of Granting/Revoking Permissions in the Code

## Visual Summary

```

┌────────────────────────────────────────────────────────────────────┐
│                    HOW PERMISSIONS WORK                            │
└────────────────────────────────────────────────────────────────────┘

CURRENTLY (ALREADY EXISTS):
    ✓ GRANT permissions
    ✗ REVOKE permissions (NOT IMPLEMENTED YET)

```

---


## 1. GRANT PERMISSIONS - ALREADY EXISTS ✓


### Location: `immich_autotag/albums/album_collection_wrapper.py`


**Line 92-113**: Function `find_or_create_album()`

```python
# Line 92: Imports the API function
from immich_client.api.albums import add_users_to_album, create_album

# Line 113: Calls the function to ADD users
add_users_to_album.sync(
    id=album.id,
    client=client,
    body=AddUsersDto(
        album_users=[
            AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)
        ]
    ),
)
```


**When is it executed?**
- When a new album is created
- The owner is added as EDITOR


**What matters here?**
- `add_users_to_album`: Immich API function that **ADDS** users to an album
- `AddUsersDto`: DTO with a list of users and roles

---


## 2. REVOKE PERMISSIONS - NOT IMPLEMENTED YET ❌


**Where should it go?**

To keep consistency with the project structure, it should go in:
1. `immich_autotag/albums/album_collection_wrapper.py` (new method)
    - Or better, in a new package `immich_autotag/permissions/`

**How would it be implemented?**

```python
# New function in album_collection_wrapper.py or permissions/

def remove_user_from_album(client, album_id: str, user_id: str):
    """Removes a user from an album."""
    from immich_client.api.albums import remove_user_from_album as api_remove
    
    api_remove.sync(
        id=album_id,
        user_id=user_id,
        client=client
    )
```

---

## 3. FLUJO ACTUAL (Phase 1 - Dry-run)

```
┌─────────────────────────────────────────────────┐
│  immich_autotag/entrypoint.py                   │
│  _process_album_permissions()                   │  ← Detection only
│                                                 │
│  - Reads config                                 │
│  - Resolves policies (resolver)                 │
│  - Logs results                                 │
│  - Registers in modification_report             │
│                                                 │
│  ❌ DOES NOT MAKE REAL API CALLS                │
└─────────────────────────────────────────────────┘
```

---

## 4. FLUJO PHASE 2 (PLANEADO - Sincronización)

```
┌──────────────────────────────────────────────────────────┐
│  immich_autotag/entrypoint.py                            │
│  _execute_album_permissions() ← NUEVA FUNCIÓN PHASE 2    │
│                                                          │
│  For each album:                                      │
│    ├─ Get resolved policy (resolver)                  │
│    │                                                  │
│    ├─ Get CURRENT members (API)                       │
│    │  └─ album.get_user_shares()  ← NOT IMPLEMENTED   │
│    │                                                  │
│    ├─ COMPARE:                                        │
│    │  ├─ Members to ADD = config - current            │
│    │  └─ Members to REMOVE = current - config         │
│    │                                                  │
│    ├─ ADD: add_users_to_album.sync() ✓ EXISTS         │
│    │  └─ Report: ALBUM_PERMISSION_SHARED              │
│    │                                                  │
│    └─ REMOVE: remove_user_from_album.sync() ❌ TODO   │
│       └─ Report: ALBUM_PERMISSION_REMOVED             │
└──────────────────────────────────────────────────────────┘
```

---

## 5. DÓNDE ESTÁ LA API DE IMMICH

**Archivo**: Dentro de `immich-client/` (cliente de la API)

```
immich-client/
├── immich_client/
│   └── api/
│       └── albums.py          ← Here are the functions
```

**Funciones disponibles en `albums.py`:**
- ✅ `add_users_to_album()` - PONER usuarios
- ❌ `remove_user_from_album()` - QUITAR usuarios (necesita verificar si existe)
- ✅ `get_album_users()` o similar - OBTENER usuarios actuales

---

## 6. CÓDIGO ACTUAL QUE USA PERMISOS

### Crear Álbum + Poner Permisos
**Archivo**: `immich_autotag/albums/album_collection_wrapper.py:92-113`

```python
from immich_client.api.albums import add_users_to_album, create_album

album = create_album.sync(client=client, body=CreateAlbumDto(...))
add_users_to_album.sync(
    id=album.id,
    client=client,
    body=AddUsersDto(
        album_users=[AlbumUserAddDto(user_id=user_id, role=AlbumUserRole.EDITOR)]
    ),
)
```

**Resultado**: ✅ Usuario añadido como EDITOR al álbum

---

## 7. TAREAS PENDIENTES PARA PHASE 2

```
NECESARIOS PARA IMPLEMENTAR:

1. ✓ Evento ALBUM_PERMISSION_REMOVED - YA AÑADIDO
2. ✓ Documentación de sincronización - YA HECHA
3. ❌ Función remove_user_from_album() - TODO
4. ❌ Obtener lista de usuarios actuales en álbum - TODO
5. ❌ Lógica de sincronización en entrypoint - TODO
6. ❌ Tests de sincronización - TODO
```

---

## 8. MAPA MENTAL COMPLETO

```
PUNTO DE ENTRADA:
  entrypoint.py
  └─ run_main()
     ├─ Phase 1: _process_album_permissions()  ✓ YA EXISTE
     │  ├─ albums/album_policy_resolver.py
     │  │  └─ resolve_album_policy()
     │  └─ report/modification_report.py
     │     └─ add_album_permission_modification()
     │
     └─ Phase 2: _execute_album_permissions()  ❌ TODO
        └─ Para cada album:
           ├─ resolver: resolve_album_policy()  ✓ EXISTE
           ├─ actual: get_album_users()  ❌ IMPLEMENTAR
           ├─ sync: add_users_to_album.sync()  ✓ EXISTE
           ├─ sync: remove_user_from_album.sync()  ❌ IMPLEMENTAR
           └─ report: add_album_permission_modification()  ✓ EXISTE
```

---

## RESUMEN

| Acción | Ubicación | Estado |
|--------|-----------|--------|
| **PONER permisos** | `album_collection_wrapper.py:113` | ✅ YA FUNCIONA |
| **QUITAR permisos** | No existe | ❌ TODO Phase 2 |
| **Detectar (Phase 1)** | `entrypoint.py:_process_album_permissions()` | ✅ YA EXISTE |
| **Resolver políticas** | `albums/album_policy_resolver.py` | ✅ YA EXISTE |
| **Registrar cambios** | `report/modification_report.py` | ✅ YA EXISTE |

---

**En resumen:**
- Ahora mismo **solo existe poner permisos** (cuando creas álbumes)
- **No existe quitar permisos** (se implementará en Phase 2)
- **Phase 1 solo detecta** (sin hacer cambios reales)
- Cuando implementemos Phase 2, habrá dos nuevas funciones de sincronización
