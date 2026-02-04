

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
    def __attrs_post_init__(self):
        if not isinstance(self.module_path, ModulePath):
            raise TypeError(f"module_path must be a ModulePath instance, got {type(self.module_path)}")





    def __str__(self):
        return self.module_path.as_dotstring()
