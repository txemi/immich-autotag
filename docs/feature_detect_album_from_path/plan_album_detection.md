# Plan de mejora para la detección y gestión de álbumes

## Peticiones del usuario

1. **Evitar que el nombre del fichero se use como nombre de álbum**
   - Actualmente, si la lógica de carpetas falla o no encuentra una carpeta válida, puede acabar usando el nombre del fichero como nombre de álbum.
   - Se debe asegurar que solo se utilicen nombres de carpetas, nunca el nombre del fichero.

2. **Álbumes creados pero no visibles/accesibles**
   - Se crean álbumes vía API, pero no aparecen en la interfaz o no tienes acceso.
   - Diagnóstico: ¿existen realmente? ¿están asignados a algún usuario? ¿hay delay o bug en Immich?
   - Solución: Verificar existencia vía API, comprobar usuarios asignados, asignar usuario si es necesario, y registrar la creación/asignación en el log.

3. **Adaptar el sistema de log para registrar acciones sobre álbumes**
   - El log actual solo registra acciones sobre tags.
   - Se debe generalizar para soportar diferentes entidades (tag, album, etc.) y acciones (add, remove, create, rename, ...).
   - Propuesta de estructura de log:

| datetime           | entity_type | action   | asset_id | asset_name | album_id | album_name | tag_name | user | details | link |
|--------------------|-------------|----------|----------|------------|----------|------------|----------|------|---------|------|
| 2025-12-23T12:34   | album       | create   | ...      | ...        | ...      | ...        |          | ...  | ...     | ...  |
| 2025-12-23T12:35   | album       | rename   | ...      | ...        | ...      | ...        |          | ...  | old_name=..., new_name=... | ... |
| 2025-12-23T12:36   | tag         | add      | ...      | ...        |          |            | autotag  | ...  |         | ...  |

- **entity_type:** 'tag', 'album', etc.
- **action:** 'add', 'remove', 'create', 'rename', etc.
- **asset_id/asset_name:** si aplica.
- **album_id/album_name:** si aplica.
- **tag_name:** si aplica.
- **user:** si aplica.
- **details:** campo libre para información adicional (por ejemplo, old_name/new_name en renombrado).
- **link:** enlace relevante (foto, álbum, etc.).

## Plan de acción sugerido

1. Refactorizar la lógica de detección de álbum para excluir el nombre de fichero.
2. Diagnosticar y corregir la visibilidad/asignación de álbumes creados.
3. Rediseñar y adaptar el sistema de log para soportar acciones sobre álbumes y tags.
4. (Opcional) Añadir tests y ejemplos de uso.

---

Este documento servirá como referencia para el desarrollo y depuración de la funcionalidad de detección y gestión de álbumes, así como para la trazabilidad de acciones en el sistema.
