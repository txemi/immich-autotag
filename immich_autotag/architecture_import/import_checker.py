"""
import_checker.py

Defines the ArchitectureImportChecker class, a custom meta path finder
for enforcing architecture rules on imports at runtime.
Allows installing a hook in sys.meta_path that validates imports according to rules
defined for the Immich-autotag project.
"""
import importlib.machinery
from typing import Optional

from immich_autotag.architecture_import.rule_evaluator import evaluate_import_rules
from immich_autotag.config.internal_config import ENABLE_ARCHITECTURE_IMPORT_HOOK
from .rules import (
    enforce_immich_api_import_rule,
    enforce_immich_proxy_import_rule,
    enforce_logging_proxy_import_rule,
)


class ArchitectureImportChecker:
    """
    Custom meta path finder for enforcing architecture rules on imports.
    Allows installing a hook in sys.meta_path that validates imports according to rules
    defined for the Immich-autotag project, ensuring architectural integrity at runtime.
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
        from .module_path import ModulePath
        ci = ModulePath.from_stack()
        if ci is None:
            raise RuntimeError("ArchitectureImportChecker: Could not determine caller module path (ci is None). Defensive fail-fast.")
        #if False and ci.is_outside_project():
        #    return None
        imported_module = ModulePath.from_dotstring(fullname)
        evaluate_import_rules(imported_module, ci)
        return None

