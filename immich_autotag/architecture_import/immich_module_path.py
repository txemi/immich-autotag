
"""
immich_module_path.py

Defines the ImmichModulePath class, which extends ModulePath with project-specific utilities
for the architecture and import rules of the Immich-autotag project.
Allows semantic queries about subpackage and core membership within the project.
"""
import attrs
from .module_path import ModulePath

@attrs.define(frozen=True, auto_attribs=True, slots=True)
class ImmichModulePath(ModulePath):
    """
    Extends ModulePath with utilities specific to the Immich-autotag project.
    Allows checking if a module belongs to the core or a specific subpackage,
    and is the entry point for architecture rules specific to the Immich domain.
    """

    @classmethod
    def from_path(cls, path):
        # Override to ensure ImmichModulePath is returned
        from pathlib import Path
        if not isinstance(path, Path):
            path = Path(path)
        return cls(tuple(path.with_suffix('').parts))

    def is_core_module(self) -> bool:
        # Determina si el módulo es del core de immich_autotag
        return self.parts[:1] == ("immich_autotag",)

    def is_in_subpackage(self, subpackage: str) -> bool:
        # Comprueba si el módulo está en un subpaquete concreto
        return subpackage in self.parts

    # Aquí puedes añadir más métodos específicos del dominio Immich

    @classmethod
    def get_root_package_path(cls) -> "ImmichModulePath":
        """
        Returns the root package as an ImmichModulePath (e.g., ImmichModulePath(('immich_autotag',)))
        """
        from pathlib import Path
        name = Path(__file__).resolve().parent.name
        return cls.from_dotstring(name)

    def is_outside_root_package(self) -> bool:
        """
        Returns True if this module path is outside the root package.
        """
        root_path = self.get_root_package_path()
        return not self.parts or self.parts[0] != root_path.parts[0]
    