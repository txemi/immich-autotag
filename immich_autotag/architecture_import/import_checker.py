import importlib.machinery
from typing import Optional

from immich_autotag.config.internal_config import ENABLE_ARCHITECTURE_IMPORT_HOOK

from .caller_info import CallerInfo
from .fullname_info import FullnameInfo
from .rules import (
    enforce_immich_api_import_rule,
    enforce_immich_proxy_import_rule,
    enforce_logging_proxy_import_rule,
)


class ArchitectureImportChecker:
    """
    Custom meta path finder for enforcing import architecture rules.
    """

    @staticmethod
    def install_architecture_import_hook():
        import sys

        from immich_autotag.config.internal_config import (
            ENABLE_ARCHITECTURE_IMPORT_HOOK,
        )

        if not ENABLE_ARCHITECTURE_IMPORT_HOOK:
            return
        # Avoid double installation
        if not any(isinstance(f, ArchitectureImportChecker) for f in sys.meta_path):
            sys.meta_path.insert(0, ArchitectureImportChecker())

    def find_spec(
        self,
        fullname: str,
        path: Optional[object] = None,
        target: Optional[object] = None,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        # If the import is outside our project, skip restrictions
        if not ENABLE_ARCHITECTURE_IMPORT_HOOK:
            return None
        ci = CallerInfo.from_stack()
        if ci is None:
            return None
        if ci.is_outside_project():
            return None

        fni = FullnameInfo(fullname)
        enforce_immich_api_import_rule(fni, ci)
        enforce_immich_proxy_import_rule(fni, ci)
        enforce_logging_proxy_import_rule(fni, ci)
        return None
