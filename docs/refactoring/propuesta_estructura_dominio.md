# Propuesta de Nueva Organización de Código: Immich AutoTag

Este informe propone una estructura alternativa basada en dominios/funcionalidades, comparando la ubicación actual de cada fichero relevante con su destino recomendado. El objetivo es lograr claridad, escalabilidad y profesionalismo.

## Tabla de Migración Sugerida

| Fichero Actual                                                        | Nueva Ubicación Sugerida                                 | Justificación                                    |
|-----------------------------------------------------------------------|----------------------------------------------------------|--------------------------------------------------|
| main.py                                                               | main.py (sin cambios)                                    | Solo punto de entrada                            |
| immich_autotag/entrypoint.py                                          | immich_autotag/app.py                                   | Lógica de arranque principal                     |
| immich_autotag/core/immich_context.py                                 | immich_autotag/context/immich_context.py                 | Contexto de ejecución                            |
| immich_autotag/core/album_collection_wrapper.py                       | immich_autotag/albums/collection.py                      | Lógica de álbumes                                |
| immich_autotag/core/album_response_wrapper.py                         | immich_autotag/albums/response_wrapper.py                | Lógica de álbumes                                |
| immich_autotag/core/album_folder_analyzer.py                          | immich_autotag/albums/folder_analyzer.py                 | Lógica de álbumes                                |
| immich_autotag/core/asset_response_wrapper.py                         | immich_autotag/assets/response_wrapper.py                | Lógica de assets                                 |
| immich_autotag/core/tag_collection_wrapper.py                         | immich_autotag/tags/collection.py                        | Lógica de tags                                   |
| immich_autotag/core/tag_modification_report.py                        | immich_autotag/tags/modification_report.py               | Lógica de tags                                   |
| immich_autotag/core/match_classification_result.py                    | immich_autotag/classification/match_result.py            | Lógica de clasificación                          |
| immich_autotag/utils/process_assets.py                                | immich_autotag/assets/process.py                         | Procesamiento de assets                          |
| immich_autotag/utils/process_single_asset.py                          | immich_autotag/assets/process_single.py                  | Procesamiento de assets                          |
| immich_autotag/utils/asset_validation.py                              | immich_autotag/assets/validation.py                      | Validación de assets                             |
| immich_autotag/utils/list_albums.py                                   | immich_autotag/albums/list.py                           | Listado de álbumes                               |
| immich_autotag/utils/list_tags.py                                     | immich_autotag/tags/list.py                             | Listado de tags                                  |
| immich_autotag/utils/helpers.py                                       | immich_autotag/common/helpers.py                        | Utilidades generales                             |
| immich_autotag/utils/get_all_assets.py                                | immich_autotag/assets/get_all.py                        | Utilidad de assets                               |
| immich_autotag/utils/print_asset_details.py                           | immich_autotag/assets/print_details.py                  | Utilidad de assets                               |
| immich_autotag/utils/print_tags.py                                    | immich_autotag/tags/print_tags.py                       | Utilidad de tags                                 |
| immich_autotag/config/user.py                                         | immich_autotag/config/user.py                           | Configuración usuario                            |
| immich_autotag/config/user_config_template.py                         | immich_autotag/config/user_config_template.py            | Configuración usuario (plantilla)                |
| immich_autotag/config/internal_config.py                              | immich_autotag/config/internal_config.py                 | Configuración interna                            |
| scripts/clean_pycache.sh                                              | scripts/clean_pycache.sh                                 | Script de limpieza                               |
| immich_api_examples/immich_api_example_read_asset_tags_albums.py      | examples/immich_api_example_read_asset_tags_albums.py    | Ejemplo de uso                                   |
| immich_api_examples/run_test_asset_albums_tags.sh                     | examples/run_test_asset_albums_tags.sh                   | Ejemplo de uso                                   |


## Notas sobre la estructura propuesta
- **Por dominio/feature:** Cada carpeta representa una parte funcional del dominio (albums, assets, tags, classification, context, common).
- **`common/`**: Para helpers/utilidades realmente genéricas.
- **`examples/`**: Para scripts de ejemplo y pruebas de integración.
- **`scripts/`**: Para utilidades de mantenimiento y automatización.
- **`config/`**: Solo configuración.
- **`main.py`**: Solo punto de entrada, sin lógica.

## Ventajas
- Más fácil de navegar y escalar.
- Cada módulo tiene un propósito claro.
- Facilita la colaboración y el onboarding.

## Siguientes pasos sugeridos
1. Revisar la tabla y ajustar según necesidades reales del dominio.
2. Migrar los ficheros siguiendo la tabla (puede hacerse por lotes o progresivamente).
3. Actualizar los imports y la documentación.
4. Añadir un README en cada subcarpeta explicando su propósito.

---

**Este informe es una propuesta. Si quieres, puedo ayudarte a automatizar la migración o a generar los README para cada subcarpeta.**
