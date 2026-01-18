"""
YAML config generator with comments from Pydantic model descriptions.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from typeguard import typechecked


@typechecked
def generate_yaml_with_comments(model: type[BaseModel], filename: str | Path):
    lines = []
    # Docstring de la clase como comentario inicial
    if model.__doc__:
        for line in model.__doc__.strip().splitlines():
            lines.append(f"# {line}")
    for name, field in model.model_fields.items():
        desc = field.field_info.description
        if desc:
            lines.append(f"# {desc}")
        value = field.default if field.default is not None else ""
        # Formateo básico para strings y None
        if isinstance(value, str):
            value = f'"{value}"'
        elif value is None:
            value = ""
        lines.append(f"{name}: {value}")
        lines.append("")  # Línea en blanco entre campos
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
