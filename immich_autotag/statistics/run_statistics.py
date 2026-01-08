from typeguard import typechecked

"""
run_statistics.py

Modelo de datos para estadísticas de ejecución, serializable a YAML.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field



# Tipado estricto para los contadores de etiquetas de salida
class OutputTagCounter(BaseModel):
    total: int = 0
    added: int = 0
    removed: int = 0
    errors: int = 0  # New: count errors for this tag

# Tipado estricto para los contadores de álbumes de salida
class OutputAlbumCounter(BaseModel):
    total: int = 0
    assigned: int = 0
    removed: int = 0
    errors: int = 0



class RunStatistics(BaseModel):

    update_asset_date_count: int = Field(0, description="Number of asset date updates")

    total_assets: Optional[int] = Field(
        None, description="Total de elementos reportados por el sistema al inicio"
    )
    max_assets: Optional[int] = Field(
        None,
        description="Máximo de elementos a procesar en esta ejecución (None = todos)",
    )
    skip_n: Optional[int] = Field(
        None, description="Número de elementos a saltar al inicio (offset)"
    )

    last_processed_id: Optional[str] = Field(
        None, description="ID of the last processed asset"
    )
    count: int = Field(0, description="Number of processed assets")
    started_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    finished_at: Optional[datetime] = None
    extra: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible field for future stats"
    )
    output_tag_counters: Dict[str, OutputTagCounter] = Field(
        default_factory=dict, description="Contadores por etiqueta de salida"
    )
    output_album_counters: Dict[str, OutputAlbumCounter] = Field(
        default_factory=dict, description="Contadores por álbum de salida"
    )
    progress_description: Optional[str] = Field(
        None, description="Descripción textual del progreso actual (porcentaje, tiempo estimado, etc.)"
    )
    @typechecked
    def to_yaml(self) -> str:
        return yaml.safe_dump(
            self.model_dump(),
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )

    @classmethod
    @typechecked
    def from_yaml(cls, data: str) -> "RunStatistics":
        return cls.model_validate(yaml.safe_load(data))
    @typechecked
    def format_progress(self) -> str:
        """
        Devuelve el progreso en formato 'actual/total (porcentaje%)'.
        Si no hay total, devuelve solo el actual.
        """
        total = self.total_assets or self.max_assets
        current = self.count
        if total:
            percent = (current / total) * 100
            return f"{current}/{total} ({percent:.1f}%)"
        return f"{current}"