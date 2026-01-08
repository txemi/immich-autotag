"""
user_real_config_pydantic.py

Configuración real del usuario expresada directamente como instancias de modelos Pydantic.
Permite discutir y validar el modelo en código antes de serializar a YAML.

*NOTA: Esta configuración como código es temporal y está pensada para facilitar el refactor y la validación de modelos. El objetivo final es migrar a YAML u otro formato estándar, pero mientras tanto, toda la lógica y comentarios relevantes se mantienen aquí.*
"""

from immich_autotag.config.experimental_config.models import (
    ServerConfig,
    ClassificationRule,
    Conversion,
    AutoTagsConfig,
    AdvancedFeatureConfig,
    FeaturesConfig,
    UserConfig,
    AlbumDetectionFromFoldersConfig,
    DateCorrectionConfig,
)

# Instancia de la configuración real del usuario.
# Instancia de la configuración real
user_real_config = UserConfig(
    # -------------------------------------------------------------------------
    # API y conexión: datos de acceso a Immich
    # host: Dominio o IP de Immich
    # port: Puerto donde escucha Immich
    # api_key: Clave API de Immich
    server=ServerConfig(
        host="immich.ad3.lab",
        port=2283,
        api_key="j88ctYwFEBXt4p7Hed8YOq6ATjNMZeJDVvLtWvo",
    ),
    # -------------------------------------------------------------------------
    # FILTRO DE ASSETS: lista de enlaces o IDs de assets a procesar.
    # Si está vacía, se procesan todos los assets. Si no, solo los indicados y logging detallado.
    filter_out_asset_links=[],
    # -------------------------------------------------------------------------
    # CLASIFICACIÓN Y REGLAS:
    # Reglas para clasificar assets por tags o patrones de nombre de álbum.
    # Ejemplo: solo los álbumes que empiezan por fecha (YYYY-, YYYY-MM, YYYY-MM-DD) se consideran "eventos".
    classification_rules=[
        ClassificationRule(
            tag_names=[
                "meme",  # (LEGACY) Meme: imágenes humorísticas, sin prefijo. Compatibilidad.
                "adult_meme",  # (LEGACY) Meme adulto: contenido NSFW, sin prefijo. Compatibilidad.
                "autotag_input_ignore",  # Ignorar: fotos descartadas del flujo principal.
                "autotag_input_meme",  # Memes/jokes subidos indiscriminadamente, no eventos.
                "autotag_input_adult_meme",  # Memes/adultos NSFW, separar del entorno familiar.
                "autotag_input_pending_review",  # Pendiente de revisión: decidir destino.
            ]
        ),
        ClassificationRule(
            album_name_patterns=[
                r"^\d{4}-(\d{2}(-\d{2})?)?"
            ]  # Solo álbumes con nombre de fecha son "eventos"
        ),
    ],
    # -------------------------------------------------------------------------
    # CONVERSIONES DE TAGS: mapeo de tags antiguos a nuevos (compatibilidad/refactor)
    conversions=[
        Conversion(
            source=ClassificationRule(tag_names=["meme"]),
            destination=ClassificationRule(tag_names=["autotag_input_meme"]),
        ),
        Conversion(
            source=ClassificationRule(tag_names=["adult_meme"]),
            destination=ClassificationRule(tag_names=["autotag_input_adult_meme"]),
        ),
    ],
    # -------------------------------------------------------------------------
    # TAGS DE SALIDA Y CONFLICTOS:
    # Configuración de tags automáticos para activos no clasificados, conflictos, duplicados, etc.
    # Todos los tags usan guiones bajos '_' (no jerarquía real) para evitar problemas con la API de Immich.
    auto_tags=AutoTagsConfig(
        enabled=True,
        category_unknown="autotag_output_unknown",  # Activos no asignados a ningún evento
        category_conflict="autotag_output_conflict",  # Activos en más de un evento (conflicto)
        duplicate_asset_album_conflict="autotag_output_duplicate_asset_album_conflict",  # Duplicados con conflicto de álbum
        duplicate_asset_classification_conflict="autotag_output_duplicate_asset_classification_conflict",  # Duplicados con conflicto de clasificación
        duplicate_asset_classification_conflict_prefix="autotag_output_duplicate_asset_classification_conflict_",  # Prefijo para conflictos de grupo
    ),
    # -------------------------------------------------------------------------
    # FEATURES Y FLAGS: activar/desactivar funcionalidades avanzadas
    features=FeaturesConfig(
        enable_album_detection=True,  # Detección de álbumes por lógica estándar
        enable_tag_suggestion=False,  # Sugerencia automática de tags (desactivado)
        advanced_feature=AdvancedFeatureConfig(enabled=True, threshold=0.8),
        enable_album_name_strip=True,  # Limpia espacios en nombres de álbumes
        album_detection_from_folders=AlbumDetectionFromFoldersConfig(
            enabled=False,  # Crear álbumes a partir de carpetas (desactivado)
            excluded_paths=[r"whatsapp"],  # Excluir carpetas por patrón
        ),
        date_correction=DateCorrectionConfig(
            enabled=False,  # Corrección de fechas por nombre de archivo/carpeta
            extraction_timezone="UTC",  # Zona horaria para extracción de fechas
        ),
        enable_checkpoint_resume=False,  # Reanudar desde último asset procesado
    ),
)

if __name__ == "__main__":
    # Mostrar la configuración cargada y validada
    import pprint

    pprint.pprint(user_real_config.model_dump())
