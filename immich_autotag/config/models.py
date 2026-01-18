"""
models.py

Pydantic models for the new structured configuration (experimental).
"""

from typing import List, Optional
from enum import Enum

# Enum para modo de conversión
class ConversionMode(str, Enum):
    MOVE = "move"   # MOVE: Cuando se aplica la conversión, los valores de destino sustituyen a los de origen. Es decir, las etiquetas y álbumes de origen se eliminan y se asignan los de destino. (Comportamiento clásico de "convertir" o "mover")
    COPY = "copy"   # COPY: Cuando se aplica la conversión, los valores de destino se añaden, pero los de origen se mantienen. Es decir, se agregan las etiquetas y álbumes de destino sin eliminar los de origen. (Comportamiento tipo "copiar")

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """
    Configuration for connecting to the Immich server API.
    Includes connection details and authentication key.
    """
    model_config = {"extra": "forbid"}
    host: str = Field(..., description="Immich server host (e.g., 'localhost' or IP address)")
    port: int = Field(..., description="Immich server port (e.g., 2283)")
    api_key: str = Field(..., description="API key for authenticating with the Immich server")


# Unified classification rule: can be by tag_names or album_name_patterns
from typing import Optional


class ClassificationRule(BaseModel):
    model_config = {"extra": "forbid"}
    tag_names: Optional[List[str]] = None
    album_name_patterns: Optional[List[str]] = None
    asset_links: Optional[List[str]] = None

    @classmethod
    def __get_pydantic_core_schema__(cls, *args, **kwargs):
        # Use the default schema, but add a custom validator
        from pydantic import GetCoreSchemaHandler
        from pydantic import core_schema
        schema = super().__get_pydantic_core_schema__(*args, **kwargs)
        def at_least_one_present(values):
            if (
                (not values.get('tag_names'))
                and (not values.get('album_name_patterns'))
                and (not values.get('asset_links'))
            ):
                raise ValueError(
                    'At least one of tag_names, album_name_patterns, or asset_links must be specified and non-empty.'
                )
            return values
        return core_schema.with_validator(schema, at_least_one_present)


class FilterConfig(BaseModel):
    """
    Filtro para limitar el conjunto de elementos a procesar.
    - filter_in: filtro positivo; solo se procesarán los elementos que cumplan alguna de las reglas indicadas.
    - filter_out: filtro negativo; se excluirán del procesamiento los elementos que cumplan alguna de las reglas indicadas.
    Si ambos están vacíos, se procesan todos los elementos.
    """
    model_config = {"extra": "forbid"}
    filter_in: List[ClassificationRule] = Field(default_factory=list)
    filter_out: List[ClassificationRule] = Field(default_factory=list)


class Destination(BaseModel):
    """
    Representa las acciones a realizar sobre activos (fotos o vídeos).
    Permite especificar a qué álbumes y con qué etiquetas se deben asociar los activos afectados por una conversión.
    """
    model_config = {"extra": "forbid"}
    album_names: Optional[List[str]] = None
    tag_names: Optional[List[str]] = None

class Conversion(BaseModel):
    """
    Permite definir reglas para aplicar automáticamente etiquetas o álbumes a los elementos (fotos o vídeos) que cumplan ciertas condiciones.
    Se usa en el procesado de autotag para transformar la clasificación de los activos según reglas declarativas.
    """
    model_config = {"extra": "forbid"}
    source: ClassificationRule
    destination: Destination
    mode: Optional[ConversionMode] = ConversionMode.MOVE


class ClassificationConfig(BaseModel):
    """
    Permite al usuario definir las categorías de clasificación que desea utilizar en la aplicación.
    Cada regla define una categoría (por tags, patrones de álbum, etc). El sistema etiquetará automáticamente:
    - Los elementos que no pertenezcan a ninguna categoría (usando autotag_unknown)
    - Los elementos que pertenezcan a más de una categoría (usando autotag_conflict)
    Así, el usuario puede detectar fácilmente activos sin clasificar o con conflicto y resolverlos manualmente.
    """
    model_config = {"extra": "forbid"}
    rules: List[ClassificationRule] = Field(default_factory=list)
    autotag_unknown: Optional[str] = None
    autotag_conflict: Optional[str] = None


class DateCorrectionConfig(BaseModel):
    """
    Configuración para la corrección de fechas de los assets.
    Si está activado, el sistema intentará obtener una fecha más precisa que la que tiene Immich:
    - Usando la fecha de duplicados (si existe y es más fiable)
    - Extrayendo la fecha del nombre del fichero si sigue patrones conocidos (por ejemplo, fotos de WhatsApp o Android)
    - Usando la zona horaria especificada para ajustar la fecha extraída
    """
    model_config = {"extra": "forbid"}
    enabled: bool
    extraction_timezone: str


class AlbumDateConsistencyConfig(BaseModel):
    """Configuration for album date consistency checks.

    This check compares the asset's taken date with its album's date
    and tags mismatches for user review.
    """

    model_config = {"extra": "forbid"}
    enabled: bool = True
    autotag_album_date_mismatch: str = "autotag_album_date_mismatch"
    threshold_days: int = 180


class DuplicateProcessingConfig(BaseModel):
    """
    Configuración para el procesamiento de duplicados.
    Se aprovechan los duplicados detectados por Immich para identificar discrepancias entre los distintos elementos duplicados.
    Esto permite detectar y etiquetar diferencias en la fecha, la clasificación o los álbumes, ya que en principio todos los duplicados deberían coincidir en estos aspectos.
    """
    model_config = {"extra": "forbid"}
    autotag_album_conflict: Optional[str] = None
    autotag_classification_conflict: Optional[str] = None
    autotag_classification_conflict_prefix: Optional[str] = None
    autotag_album_detection_conflict: Optional[str] = None
    date_correction: DateCorrectionConfig


# Grouping of coupled fields in subclasses
class AlbumDetectionFromFoldersConfig(BaseModel):
    """
    Configuration for automatic album creation from folders containing a date in their name.
    
    If enabled, the system will scan folder paths (not just the immediate parent) for date patterns.
    For each folder that includes a date, a daily album will be created for the assets within.
    Folders listed in 'excluded_paths' will be ignored.
    """
    model_config = {"extra": "forbid"}
    enabled: bool = Field(..., description="Enable automatic album creation from folders with a date in their name.")
    excluded_paths: List[str] = Field(..., description="List of folder paths to exclude from album detection.")


class PerformanceConfig(BaseModel):
    """Performance and debugging settings."""
    model_config = {"extra": "forbid"}
    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )


class UserGroup(BaseModel):
    """Represents a logical group of users for album sharing."""
    model_config = {"extra": "forbid"}
    name: str = Field(..., description="Group name (e.g., 'familia', 'amigos')")
    description: Optional[str] = Field(
        None, description="Human-readable description of the group"
    )
    members: List[str] = Field(
        ...,
        description="List of member emails or user IDs",
        min_items=1,
    )


class AlbumSelectionRule(BaseModel):
    """Rule for selecting albums by keyword and assigning to groups."""
    model_config = {"extra": "forbid"}
    name: str = Field(..., description="Rule name (e.g., 'Share with Familia')")
    keyword: str = Field(
        ...,
        description="Keyword to match in album name (case-insensitive word matching)",
    )
    groups: List[str] = Field(
        ..., description="List of group names to assign to matching albums", min_items=1
    )
    access: str = Field(
        default="view",
        description="Permission level: 'view', 'edit', or 'admin'",
        pattern="^(view|edit|admin)$",
    )


class AlbumPermissionsConfig(BaseModel):
    """Configuration for automatic album permission assignment."""
    model_config = {"extra": "forbid"}
    enabled: bool = Field(default=False, description="Enable album permission feature")
    user_groups: Optional[List[UserGroup]] = Field(
        None, description="Define logical user groups"
    )
    selection_rules: Optional[List[AlbumSelectionRule]] = Field(
        None, description="Rules for matching albums to groups"
    )
    log_unmatched: bool = Field(
        default=False,
        description="Log albums that don't match any rule (can be noisy)",
    )


class PerformanceConfig(BaseModel):
    """Performance and debugging settings."""

    enable_type_checking: bool = Field(
        default=False,
        description="Enable @typechecked runtime type validation. Disable in production for ~50% performance improvement.",
    )

# --- Skip/Resume configuration ---
class SkipConfig(BaseModel):
    """
    Configuración para saltar y limitar el procesamiento de elementos.
    Permite especificar cuántos elementos iniciales se deben saltar (skip_n).
    Si resume_previous es True, el valor de skip_n se puede tomar automáticamente de la ejecución anterior (por ejemplo, para reanudar tras un fallo).
    El campo max_items permite limitar la cantidad máxima de elementos a procesar en la ejecución actual.
    """
    model_config = {"extra": "forbid"}
    skip_n: int = Field(default=0, description="Número de elementos a saltar al procesar.")
    resume_previous: bool = Field(default=True, description="Si se debe continuar desde la ejecución anterior.")
    max_items: Optional[int] = Field(default=None, description="Máximo número de elementos a procesar en esta ejecución. Si es None, no hay límite.")
    # antiguo     enable_checkpoint_resume: bool


class UserConfig(BaseModel):
    """
    Objeto principal de configuración del sistema Immich autotag.
    Puede ser construido directamente en Python o deserializado/serializado desde y hacia un fichero de texto (YAML o Python).
    Incluye todos los parámetros y bloques de configuración necesarios para el funcionamiento del sistema.
    """
    model_config = {"extra": "forbid"}
    server: ServerConfig
    enable_album_name_strip: bool
    skip: SkipConfig = Field(
        ...,
        description="Configuration for skipping items and resuming previous executions."
    )
    filters: Optional[FilterConfig] = None
    conversions: List[Conversion]
    classification: ClassificationConfig
    duplicate_processing: Optional[DuplicateProcessingConfig] = None
    album_date_consistency: Optional[AlbumDateConsistencyConfig] = None
    album_detection_from_folders: AlbumDetectionFromFoldersConfig
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    album_permissions: Optional[AlbumPermissionsConfig] = Field(
        None, description="Configuration for automatic album permission assignment"
    )
    create_album_from_date_if_missing: bool = False
