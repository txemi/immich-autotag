# Refactorización propuesta: `immich_autotag/assets/process_single_asset.py`

| Clase/Método/Función                  | Fichero actual                                      | Fichero destino propuesto                                 |
|---------------------------------------|-----------------------------------------------------|----------------------------------------------------------|
| DuplicateAlbumsInfo                   | assets/process_single_asset.py                      | assets/duplicates/duplicate_albums_info.py                |
| get_album_from_duplicates             | assets/process_single_asset.py                      | assets/duplicates/get_album_from_duplicates.py            |
| AlbumDecision                         | assets/process_single_asset.py                      | assets/albums/album_decision.py                           |
| decide_album_for_asset                | assets/process_single_asset.py                      | assets/albums/decide_album_for_asset.py                   |
| analyze_and_assign_album              | assets/process_single_asset.py                      | assets/albums/analyze_and_assign_album.py                 |
| _process_album_detection              | assets/process_single_asset.py                      | assets/albums/process_album_detection.py                  |
| analyze_duplicate_classification_tags  | assets/duplicate_tag_logic/analyze_duplicate_classification_tags.py | (sin cambio)                                 |
| process_single_asset                  | assets/process_single_asset.py                      | assets/process/process_single_asset.py                    |
| validate_and_update_asset_classification | assets/asset_validation.py                        | assets/validation/validate_and_update_asset_classification.py |

**Notas:**
- Cada clase o función relevante va en su propio fichero, salvo helpers triviales.
- Los nombres de los nuevos ficheros pueden ajustarse para mayor claridad o coherencia con el resto del proyecto.
- El objetivo es máxima trazabilidad, mantenibilidad y facilidad de testing.
- Las rutas propuestas siguen la estructura modular y de subcarpetas ya presente en el proyecto.

¿Quieres que añada justificaciones o dependencias para cada movimiento?