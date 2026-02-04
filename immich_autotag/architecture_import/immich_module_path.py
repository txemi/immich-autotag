"""
immich_module_path.py

Defines the ImmichModulePath class, which extends ModulePath with project-specific utilities
for the architecture and import rules of the Immich-autotag project.
Allows semantic queries about subpackage and core membership within the project.
"""

import attrs

from immich_autotag.architecture_import.shared_symbols import LOGGING_PROXY_MODULE_NAME

from .module_path import ModulePath


@attrs.define(frozen=True, auto_attribs=True, slots=True)
class ImmichModulePath(ModulePath):
    """
    Extends ModulePath with utilities specific to the Immich-autotag project.
    Allows checking if a module belongs to the core or a specific subpackage,
    and is the entry point for architecture rules specific to the Immich domain.
    """

    def is_proxy_module_import(self) -> bool:
        """
        Returns True if the module path includes 'immich_proxy'.
        """
        return "immich_proxy" in self.get_parts()

    def is_outside_logging_proxy(self) -> bool:
        """
        Returns True if the module path does not include all parts of the logging proxy module.
        """
        from .shared_symbols import LOGGING_PROXY_MODULE_NAME

        logging_proxy_parts = tuple(LOGGING_PROXY_MODULE_NAME.split("."))
        return not all(part in self.get_parts() for part in logging_proxy_parts)


    @classmethod
    def from_path(cls, path):
        # Override to ensure ImmichModulePath is returned
        from pathlib import Path

        if not isinstance(path, Path):
            path = Path(path)
        return cls(tuple(path.with_suffix("").parts))

    def is_core_module(self) -> bool:
        # Determines if the module is part of the immich_autotag core
        return self.get_parts()[:1] == ("immich_autotag",)

    def is_in_subpackage(self, subpackage: str) -> bool:
        # Checks if the module is in a specific subpackage
        return subpackage in self.get_parts()

    # Add more Immich domain-specific methods here

    @classmethod
    def get_root_package_path(cls) -> "ImmichModulePath":
        """
        Returns the root package as an ImmichModulePath (e.g., ImmichModulePath(('immich_autotag',)))
        """
        from pathlib import Path

        name = Path(__file__).resolve().parent.parent.name
        # Always use cls.from_dotstring to ensure correct type
        aa = cls.from_dotstring(name)
        return cls.from_module_path(aa)

    def is_outside_root_package(self) -> bool:
        """
        Returns True if this module path is outside the root package.
        """
        root_path = self.get_root_package_path()
        return self.is_outside_root_of(root_path)

    @classmethod
    def from_module_path(cls, module_path: ModulePath) -> "ImmichModulePath":
        """
        Converts a ModulePath (or ImmichModulePath) to an ImmichModulePath instance.
        """
        parts = module_path.get_parts()
        return cls(parts)

    def is_immich_api_module(self) -> bool:
        """
        Returns True if this module path is part of the Immich API (client) prefix.
        """
        from .shared_symbols import IMMICH_CLIENT_PREFIX

        return self.as_dotstring().startswith(IMMICH_CLIENT_PREFIX)

    def is_import_from_immich_proxy(self) -> bool:
        """
        Returns True if the module path is from the Immich proxy prefix.
        """
        from .shared_symbols import IMMICH_PROXY_PREFIX

        return self.as_dotstring().startswith(IMMICH_PROXY_PREFIX)

    def is_import_from_logging_proxy(self) -> bool:
        return self.as_dotstring().startswith(LOGGING_PROXY_MODULE_NAME)

    def is_architecture_rules(self) -> bool:
        """
        Returns True if this module path is inside the architecture_import package (by first-level match).
        """
        # Use the actual package reference for robustness
        import immich_autotag.architecture_import
        arch_pkg_path = ImmichModulePath.from_dotstring(immich_autotag.architecture_import.__name__)
        return self.is_submodule_of(arch_pkg_path)