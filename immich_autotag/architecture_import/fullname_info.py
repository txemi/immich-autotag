

"""
imported_module_info.py

Defines the ImportedModuleInfo class, which encapsulates the imported module's path
as a ModulePath object and allows queries about its membership in relevant prefixes
for the Immich-autotag project. Used by the architecture rules system to validate imports.
"""
import attrs
from .module_path import ModulePath
from .shared_symbols import (
    IMMICH_CLIENT_PREFIX,
    IMMICH_PROXY_PREFIX,
    LOGGING_PROXY_MODULE_NAME,
)

@attrs.define(frozen=True, auto_attribs=True)
class ImportedModuleInfo:
    """
    Encapsulates the imported module's path as a ModulePath object and allows queries
    about its membership in relevant prefixes for the Immich-autotag project.
    Used by the architecture rules system to validate imports.
    """
    module_path: ModulePath

    def is_immich_api_module(self) -> bool:
        return self.module_path.as_dotstring().startswith(IMMICH_CLIENT_PREFIX)

    def is_import_from_immich_proxy(self) -> bool:
        return self.module_path.as_dotstring().startswith(IMMICH_PROXY_PREFIX)

    def is_import_from_logging_proxy(self) -> bool:
        return self.module_path.as_dotstring().startswith(LOGGING_PROXY_MODULE_NAME)

    def __str__(self):
        return self.module_path.as_dotstring()
