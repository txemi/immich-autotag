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