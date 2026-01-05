
from typeguard import typechecked

"""
run_statistics.py

Modelo de datos para estadísticas de ejecución, serializable a YAML.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic import BaseModel, Field
from typing import Dict


# Tipado estricto para los contadores de etiquetas de salida
class OutputTagCounter(BaseModel):
    total: int = 0
    added: int = 0
    removed: int = 0

class RunStatistics(BaseModel):
    total_assets: Optional[int] = Field(
        None, description="Total de elementos reportados por el sistema al inicio"
    )
    max_assets: Optional[int] = Field(
        None, description="Máximo de elementos a procesar en esta ejecución (None = todos)"
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
