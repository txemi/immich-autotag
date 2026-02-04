"""
module_path.py

Defines the ModulePath class, which represents Python module paths as tuples of parts.
Allows constructing paths from strings, Path, or parts, and performing typical hierarchical operations.
This class is the base for architecture logic regarding imports and module membership.
"""
from pathlib import Path
from typing import Tuple, Union
import attrs

@attrs.define(frozen=True, auto_attribs=True, slots=True)
class ModulePath:
    """
    Represents a Python module path (e.g., 'immich_autotag.assets.process')
    as a tuple of parts. Allows constructing paths from string, Path, or parts,
    and performing hierarchical operations such as checking package membership.
    It is the base for architecture rules on imports at runtime.
    """
    parts: Tuple[str, ...]

    @classmethod
    def from_dotstring(cls, module: str) -> "ModulePath":
        return cls(tuple(module.split('.')))

    @classmethod
    def from_path(cls, path: Path) -> "ModulePath":
        # Elimina el sufijo .py y convierte a partes
        return cls(tuple(path.with_suffix('').parts))

    @classmethod
    def from_parts(cls, parts: Union[list[str], tuple[str, ...]]) -> "ModulePath":
        return cls(tuple(parts))

    def is_submodule_of(self, other: "ModulePath") -> bool:
        return self.parts[:len(other.parts)] == other.parts

    def as_dotstring(self) -> str:
        return '.'.join(self.parts)

    def as_path(self) -> Path:
        return Path(*self.parts)

    def __repr__(self) -> str:
        return f"ModulePath({self.as_dotstring()})"
