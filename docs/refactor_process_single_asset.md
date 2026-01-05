# Refactorización propuesta: `immich_autotag/assets/process_single_asset.py`


# Tabla de correspondencia: símbolo, fichero actual y destino

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
| log_execution_parameters              | assets/process_assets.py                            | assets/process/log_execution_parameters.py                | No        |
| fetch_total_assets                    | assets/process_assets.py                            | assets/process/fetch_total_assets.py                      | No        |
| resolve_checkpoint                    | assets/process_assets.py                            | assets/process/resolve_checkpoint.py                      | No        |
| register_execution_parameters         | assets/process_assets.py                            | assets/process/register_execution_parameters.py            | No        |
| perf_log                              | assets/process_assets.py                            | assets/process/perf_log.py                                | No        |
| process_assets_threadpool             | assets/process_assets.py                            | assets/process/process_assets_threadpool.py                | No        |
| process_assets_sequential             | assets/process_assets.py                            | assets/process/process_assets_sequential.py                | No        |
| log_final_summary                     | assets/process_assets.py                            | assets/process/log_final_summary.py                        | No        |
| process_assets                        | assets/process_assets.py                            | assets/process/process_assets.py                           | No        |

# Plan de ejecución para el refactor progresivo de assets

El objetivo es mover los símbolos uno a uno, probando tras cada movimiento para minimizar conflictos y asegurar que todo sigue funcionando. El orden propuesto prioriza dependencias y minimiza el riesgo de rotura.

## Tabla de símbolos a refactorizar

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
| 9     | log_execution_parameters               | Mover función a log_execution_parameters.py y actualizar imports       |
| 10    | fetch_total_assets                     | Mover función a fetch_total_assets.py y actualizar imports             |
| 11    | resolve_checkpoint                     | Mover función a resolve_checkpoint.py y actualizar imports             |
| 12    | register_execution_parameters          | Mover función a register_execution_parameters.py y actualizar imports  |
| 13    | perf_log                               | Mover función a perf_log.py y actualizar imports                       |
| 14    | process_assets_threadpool              | Mover función a process_assets_threadpool.py y actualizar imports      |
| 15    | process_assets_sequential              | Mover función a process_assets_sequential.py y actualizar imports      |
| 16    | log_final_summary                      | Mover función a log_final_summary.py y actualizar imports              |
| 17    | process_assets                         | Mover función a process_assets.py y actualizar imports                 |

**Recomendaciones:**
- Tras cada movimiento, ejecutar los tests o probar la funcionalidad relevante.
- Actualizar los imports en todos los módulos afectados tras cada paso.
- Si alguna función depende de otra que aún no se ha movido, mover primero la dependencia.
- Mantener los ficheros originales hasta que todo esté probado, luego limpiar.

**Estrategia de orden:**
- Primero mover las clases y funciones que no dependen de otras (privadas y utilitarias).
- Después, mover las funciones que dependen de las anteriores.
- Finalmente, mover las funciones principales (`process_single_asset`, `process_assets_sequential`, `process_assets_threadpool`, `process_assets`).
- Probar tras cada paso para asegurar que la aplicación nunca deja de funcionar.

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