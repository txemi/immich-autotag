# Localización EXACTA del Código de Permisos

## PONER PERMISOS (Cuando se crea un álbum)

### Archivo: `immich_autotag/albums/album_collection_wrapper.py`

```
LÍNEA  CÓDIGO
────────────────────────────────────────────────────────────────
 92    from immich_client.api.albums import add_users_to_album, ← AQUÍ se importa
 92    create_album                                              la función para PONER

 99    def find_or_create_album(                                ← FUNCIÓN que PONE permisos
 99        self, ...)

113    add_users_to_album.sync(                                ← AQUÍ es donde se PONE
       id=album.id,                                             el permiso (REAL)
       client=client,
       body=AddUsersDto(
           album_users=[
               AlbumUserAddDto(
                   user_id=user_id,
                   role=AlbumUserRole.EDITOR    ← EDITOR = lectura + edición
               )
           ]
       ),
    )
```

**¿Qué hace?**
1. Crea un álbum nuevo
2. Obtiene el ID del usuario actual
3. Llama a `add_users_to_album.sync()` 
4. Añade el usuario como EDITOR

**¿Cuándo se ejecuta?**
- Al crear un álbum nuevo en Immich

---

## QUITAR PERMISOS (NO EXISTE AÚN)

### Debería ir en: `immich_autotag/permissions/` (Phase 2)

**Implementación futura sería:**

```python
# immich_autotag/permissions/album_permission_executor.py (NUEVO)

from immich_client.api.albums import remove_user_from_album

def sync_album_permissions(client, album, resolved_policy):
    """Sincroniza permisos completos del álbum."""
    
    # 1. Obtener usuarios actuales
    current_users = get_album_members(client, album.id)  # API call
    
    # 2. Comparar
    to_add = set(resolved_policy.members) - set(current_users)
    to_remove = set(current_users) - set(resolved_policy.members)
    
    # 3. AÑADIR nuevos
    for user_email in to_add:
        add_users_to_album.sync(                         ← YA EXISTE
            id=album.id,
            client=client,
            body=AddUsersDto(
                album_users=[AlbumUserAddDto(...)]
            )
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_SHARED
        )
    
    # 4. QUITAR antiguos  ← NECESITA IMPLEMENTARSE
    for user_id in to_remove:
        remove_user_from_album.sync(                     ← TODAVÍA NO EXISTE
            id=album.id,
            user_id=user_id,
            client=client
        )
        report.add_album_permission_modification(
            kind=ModificationKind.ALBUM_PERMISSION_REMOVED
        )
```

---

## FLUJO ACTUAL (Phase 1)

### Archivo: `immich_autotag/entrypoint.py`

```
LÍNEA  CÓDIGO
────────────────────────────────────────────────────────────────
  32   def _process_album_permissions(                  ← FUNCIÓN Phase 1
  32       user_config,
  32       context: ImmichContext
  32   ) -> None:

  56   log(
  56       "[ALBUM_PERMISSIONS] Starting Phase 1..."    ← LOG: Iniciando
  56   )

  62   albums_collection = context.albums_collection    ← Lee álbumes
  64   user_groups_dict = {}                           ← Build lookup dict
  65   if album_perms_config.user_groups:
  66       for group in album_perms_config.user_groups:
  67           user_groups_dict[group.name] = group

  73   for album in albums_collection.values():         ← LOOP: cada álbum
  74       resolved_policy = resolve_album_policy(      ← RESUELVE política
  74           album_name=album.album_name,
  74           album_id=album.id,
  74           user_groups=user_groups_dict,
  74           selection_rules=album_perms_config.selection_rules
  74       )

  76   if resolved_policy.has_match:                     ← ¿Coincidió?
  77       matched_count += 1
  78       log(...)                                      ← LOG: coincidencia
  86       report.add_album_permission_modification(    ← REGISTRA evento
  86           kind=ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
  86           ...
  86       )

  107  log(                                              ← LOG: resumen final
  107      f"[ALBUM_PERMISSIONS] Summary: {matched_count}..."
  107  )
```

**¿Qué hace Phase 1?**
- Solo LEE la configuración
- Solo RESUELVE qué usuarios deberían tener acceso
- Solo REGISTRA en el report
- ❌ NO hace cambios reales en Immich

---

## DONDE ESTÁ LA RESOLUCIÓN DE POLÍTICAS

### Archivo: `immich_autotag/albums/album_policy_resolver.py`

```
LÍNEA  CÓDIGO
────────────────────────────────────────────────────────────────
  96   def resolve_album_policy(                        ← FUNCIÓN: resuelve
  96       album_name: str,
  96       album_id: str,
  96       user_groups: Dict[str, UserGroup],
  96       selection_rules: List[AlbumSelectionRule],
  96   ) -> ResolvedAlbumPolicy:

 122   for rule in selection_rules:                     ← LOOP: cada regla
 123       if _match_keyword_in_album(album_name, rule.keyword):
 124           matched_rules_names.append(rule.name)
 125           all_groups.extend(rule.groups)           ← Acumula grupos

 130   for group_name in all_groups_unique:             ← LOOP: cada grupo
 131       if group_name in user_groups:
 132           group = user_groups[group_name]
 133           all_members.extend(group.members)        ← Acumula miembros

 137   return ResolvedAlbumPolicy(                       ← RETORNA resultado
 137       album_name=album_name,
 137       matched_rules=matched_rules_names,
 137       groups=all_groups_unique,
 137       members=all_members_unique,                  ← ESTOS son los que
 137       access_level=access_level,                     deberían tener acceso
 137   )
```

**¿Qué devuelve?**
```
ResolvedAlbumPolicy(
    album_name="2024-Familia-Vacation",
    album_id="abc123",
    matched_rules=["Share Familia albums"],
    groups=["familia"],
    members=["abuelo@ex.com", "madre@ex.com"],    ← ESTOS deben tener acceso
    access_level="view",
    has_match=True
)
```

---

## DONDE SE REGISTRAN LOS CAMBIOS

### Archivo: `immich_autotag/report/modification_report.py`

```
LÍNEA  CÓDIGO
────────────────────────────────────────────────────────────────
 268   def add_album_permission_modification(           ← MÉTODO para registrar
 268       self,
 268       kind: ModificationKind,
 268       album: Optional[AlbumResponseWrapper] = None,
 268       matched_rules: Optional[list[str]] = None,
 268       groups: Optional[list[str]] = None,
 268       members: Optional[list[str]] = None,
 268       access_level: Optional[str] = None,
 268       extra: Optional[dict] = None,
 268   ) -> None:

 291   assert kind in {                                 ← VALIDA que sea
 291       ModificationKind.ALBUM_PERMISSION_RULE_MATCHED,
 291       ModificationKind.ALBUM_PERMISSION_GROUPS_RESOLVED,
 291       ModificationKind.ALBUM_PERMISSION_NO_MATCH,
 291       ModificationKind.ALBUM_PERMISSION_SHARED,    ← cuando se PONE
 291       ModificationKind.ALBUM_PERMISSION_REMOVED,   ← cuando se QUITA ✨ NUEVO
 291       ModificationKind.ALBUM_PERMISSION_SHARE_FAILED,
 291   }

 311   self.add_modification(                           ← REGISTRA en report
 311       kind=kind,
 311       album=album,
 311       extra=extra,  # Con miembros, grupos, etc.
 311   )
```

**¿Qué registra?**
- Cada decisión de permiso
- A qué álbum afecta
- Qué usuarios, grupos y reglas estuvieron involucrados
- Se guardará en `modification_report.txt`

---

## EVENTOS DISPONIBLES

### Archivo: `immich_autotag/tags/modification_kind.py`

```
LÍNEA  CÓDIGO
────────────────────────────────────────────────────────────────
  46   ALBUM_PERMISSION_RULE_MATCHED = auto()           ← Álbum coincidió
  47   ALBUM_PERMISSION_GROUPS_RESOLVED = auto()        ← Grupos resueltos
  48   ALBUM_PERMISSION_NO_MATCH = auto()               ← Sin coincidencia
  49   
  50   # Phase 2: actual sharing
  51   ALBUM_PERMISSION_SHARED = auto()                  ← Usuario AÑADIDO ✅
  52   ALBUM_PERMISSION_REMOVED = auto()                 ← Usuario REMOVIDO ✅ NUEVO
  53   ALBUM_PERMISSION_SHARE_FAILED = auto()            ← Error al añadir
```

---

## RESUMEN: DÓNDE PASA CADA COSA

| QUÉ | DÓNDE | LÍNEA | ESTADO |
|-----|-------|-------|--------|
| **Se resuelve** qué usuarios deben tener acceso | `album_policy_resolver.py` | 96-137 | ✅ |
| **Se obtienen** usuarios actuales del álbum | API Immich | — | ❌ TODO |
| **Se PONEN** nuevos permisos | `album_collection_wrapper.py` | 113 | ✅ |
| **Se QUITAN** permisos antiguos | API Immich | — | ❌ TODO |
| **Se registra** en report | `modification_report.py` | 268 | ✅ |
| **Phase 1** (detecta, sin hacer nada) | `entrypoint.py` | 32 | ✅ |
| **Phase 2** (ejecuta cambios reales) | — | — | ❌ TODO |

---

## PRÓXIMO PASO: PHASE 2

Para implementar Phase 2, necesitaremos:

1. **Obtener usuarios actuales del álbum**
   - Usar API: `get_album_users()` de Immich client
   - Extrae IDs/emails de quien tiene acceso ahora

2. **Función de sincronización**
   ```python
   # Nuevo módulo: immich_autotag/permissions/album_permission_executor.py
   
   def sync_album_permissions(client, album, resolved_policy):
       current = get_album_users(client, album.id)  # Get current
       to_add = resolved_policy.members - current    # Calculate diff
       to_remove = current - resolved_policy.members
       
       # Add new (usar add_users_to_album - YA EXISTE)
       # Remove old (usar remove_user_from_album - IMPLEMENTAR)
   ```

3. **Llamar desde entrypoint**
   ```python
   # immich_autotag/entrypoint.py
   _execute_album_permissions(manager.config, context)  # Nueva función
   ```

¿Quieres que continúe con Phase 2? 🚀
