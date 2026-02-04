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
    def is_core_module(self) -> bool:
        # Determina si el módulo es del core de immich_autotag
        return self.parts[:1] == ("immich_autotag",)

    def is_in_subpackage(self, subpackage: str) -> bool:
        # Comprueba si el módulo está en un subpaquete concreto
        return subpackage in self.parts

    # Aquí puedes añadir más métodos específicos del dominio Immich
