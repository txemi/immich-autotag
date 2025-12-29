# Date Correction Module Map

Esta tabla indica la correspondencia propuesta entre funciones/clases y sus ficheros destino en el paquete `date_correction`.

| Función/Clase                        | Fichero destino propuesto                |
|---------------------------------------|------------------------------------------|
| extract_whatsapp_date_from_path       | extract_whatsapp_date_from_path.py       |
| get_asset_date_sources                | get_asset_date_sources.py                |
| correct_asset_date                    | correct_asset_date.py                    |
| AssetDateSources (clase)              | asset_date_sources.py                    |
| AssetDateCandidates (clase)           | asset_date_candidates.py                 |
| AssetDateSourcesList (clase)          | asset_date_sources_list.py               |

- Cada fichero contendrá una única función o clase principal.
- Los métodos auxiliares ligados a una clase pueden quedarse en el mismo fichero de la clase.
- Los nombres siguen el patrón snake_case para funciones y clases.
