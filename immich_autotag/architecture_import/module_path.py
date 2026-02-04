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
    _parts: Tuple[str, ...]

    def __attrs_post_init__(self):
        # Ensure _parts is a non-empty tuple of strings
        if not isinstance(self._parts, tuple):
            raise TypeError(f"ModulePath _parts must be a tuple, got {type(self._parts)}")
        if not self._parts or len(self._parts) == 0:
            raise ValueError("ModulePath must have at least one part.")
        for p in self._parts:
            if not isinstance(p, str):
                raise TypeError(f"ModulePath parts must be strings, got {type(p)} in {self._parts}")

    def get_parts(self) -> Tuple[str, ...]:
        """
        Returns the tuple of parts of the module path.
        """
        return self._parts

    @classmethod
    def from_dotstring(cls, module: str) -> "ModulePath":
        return cls(tuple(module.split('.')))

    @classmethod
    def from_path(cls, path: Path) -> "ModulePath":
        # Removes the .py suffix and converts to parts
        return cls(tuple(path.with_suffix('').parts))

    @classmethod
    def from_parts(cls, parts: Union[list[str], tuple[str, ...]]) -> "ModulePath":
        return cls(tuple(parts))

    def is_submodule_of(self, other: "ModulePath") -> bool:
        return self.get_parts()[:len(other.get_parts())] == other.get_parts()

    def as_dotstring(self) -> str:
        return '.'.join(self.get_parts())

    def as_path(self) -> Path:
        return Path(*self.get_parts())

    def __repr__(self) -> str:
        return f"ModulePath({self.as_dotstring()})"
    def is_outside_root_of(self, other: "ModulePath") -> bool:
        """
        Returns True if this module path is outside the root of another module path.
        """
        return not self.get_parts() or not other.get_parts() or self.get_parts()[0] != other.get_parts()[0]