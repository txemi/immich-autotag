# Refactorización propuesta: `immich_autotag/assets/process_single_asset.py`

| Clase/Método/Función                  | Fichero actual                                      | Fichero destino propuesto                                 | ¿Privado? |
|---------------------------------------|-----------------------------------------------------|----------------------------------------------------------|-----------|
| DuplicateAlbumsInfo                   | assets/process_single_asset.py                      | assets/duplicates/_duplicate_albums_info.py               | Sí        |
| get_album_from_duplicates             | assets/process_single_asset.py                      | assets/duplicates/_get_album_from_duplicates.py           | Sí        |
| AlbumDecision                         | assets/process_single_asset.py                      | assets/albums/album_decision.py                           | No        |
| decide_album_for_asset                | assets/process_single_asset.py                      | assets/albums/decide_album_for_asset.py                   | No        |
| analyze_and_assign_album              | assets/process_single_asset.py                      | assets/albums/analyze_and_assign_album.py                 | No        |
| _process_album_detection              | assets/process_single_asset.py                      | assets/albums/_process_album_detection.py                 | Sí        |
| analyze_duplicate_classification_tags  | assets/duplicate_tag_logic/analyze_duplicate_classification_tags.py | (sin cambio)                                 | No        |
| process_single_asset                  | assets/process_single_asset.py                      | assets/process/process_single_asset.py                    | No        |
| validate_and_update_asset_classification | assets/asset_validation.py                        | assets/validation/validate_and_update_asset_classification.py | No        |

**Notas:**
- Los ficheros marcados como "Sí" en la columna "¿Privado?" deberían llevar guion bajo inicial en el nombre del fichero y de la función/clase.
- El resto forman parte de la API pública del paquete o subpaquete.
- Puedes ajustar según el uso real en el proyecto.

# Plan de ejecución para el refactor de process_single_asset.py

El objetivo es mover los símbolos uno a uno, probando tras cada movimiento para minimizar conflictos y asegurar que todo sigue funcionando.

| Orden | Símbolo/Fichero                       | Acción                                                                 |
|-------|----------------------------------------|------------------------------------------------------------------------|
| 1     | DuplicateAlbumsInfo                    | Mover clase a _duplicate_albums_info.py y actualizar imports           |
| 2     | get_album_from_duplicates              | Mover función a _get_album_from_duplicates.py y actualizar imports     |
| 3     | AlbumDecision                          | Mover clase a album_decision.py y actualizar imports                   |
| 4     | decide_album_for_asset                 | Mover función a decide_album_for_asset.py y actualizar imports         |
| 5     | analyze_and_assign_album               | Mover función a analyze_and_assign_album.py y actualizar imports       |
| 6     | _process_album_detection               | Mover función a _process_album_detection.py y actualizar imports       |
| 7     | process_single_asset                   | Mover función a process_single_asset.py y actualizar imports           |
| 8     | validate_and_update_asset_classification | Mover función a validate_and_update_asset_classification.py y actualizar imports |

**Recomendaciones:**
- Tras cada movimiento, ejecutar los tests o probar la funcionalidad relevante.
- Actualizar los imports en todos los módulos afectados tras cada paso.
- Si alguna función depende de otra que aún no se ha movido, mover primero la dependencia.
- Mantener los ficheros originales hasta que todo esté probado, luego limpiar.

¿Quieres que prepare el primer movimiento (DuplicateAlbumsInfo) y su actualización de imports?

# Refactorización complementaria: simplificación de process_assets

El método `process_assets` en `assets/process_assets.py` es demasiado grande y difícil de mantener. Se propone dividirlo en sub-funciones con responsabilidades claras:

| Sub-función sugerida                | Responsabilidad principal                                                                 |
|-------------------------------------|------------------------------------------------------------------------------------------|
| `log_execution_parameters`          | Loguear los parámetros de ejecución y configuración                                      |
| `fetch_total_assets`                | Consultar y registrar el total de assets disponibles                                     |
| `resolve_checkpoint`                | Calcular `last_processed_id` y `skip_n` según el modo de reanudación                     |
| `register_execution_parameters`     | Guardar en estadísticas: total_assets, max_assets, skip_n                                |
| `process_assets_threadpool`         | Procesar assets usando ThreadPoolExecutor                                                |
| `process_assets_sequential`         | Procesar assets secuencialmente (con checkpoint/resume y estadísticas)                   |
| `log_final_summary`                 | Loguear resumen final, tiempo total, y flush de reportes                                 |

### Estructura sugerida

```python
def process_assets(context: ImmichContext, max_assets: int | None = None) -> None:
    log_execution_parameters()
    total_assets = fetch_total_assets(context)
    last_processed_id, skip_n = resolve_checkpoint()
    register_execution_parameters(total_assets, max_assets, skip_n)
    if USE_THREADPOOL:
        process_assets_threadpool(context, max_assets)
    else:
        process_assets_sequential(context, max_assets, skip_n, last_processed_id)
    log_final_summary()
```

- Cada sub-función puede estar definida como función interna o externa según convenga.
- El cuerpo principal queda reducido a una secuencia clara de pasos.
- El código de logging, estadísticas y control de errores se encapsula en funciones pequeñas y reutilizables.

**Recomendación:**
- Este refactor es complementario al plan de modularización de process_single_asset.py y puede abordarse en paralelo.
- Tras aplicar ambos, el flujo de procesamiento de assets será mucho más mantenible y escalable.