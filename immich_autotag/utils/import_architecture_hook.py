"""
Import hook for architecture checks.
This module installs a custom import hook that checks every import against a set of architectural rules.
You can extend the logic to log, block, or warn about imports that violate your constraints.
"""

import importlib.machinery
import inspect
import sys
from pathlib import Path
from typing import Optional

from typeguard import typechecked

from immich_autotag.api import immich_proxy, logging_proxy
from immich_autotag.config.internal_config import ENABLE_ARCHITECTURE_IMPORT_HOOK

IMMICH_API_MODULE: str = immich_proxy.__name__
LOGGING_PROXY_MODULE: str = logging_proxy.__name__


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@typechecked
def _get_importing_module_relative_path() -> Optional[Path]:
    """
    Returns the relative path (to PROJECT_ROOT) of the first non-frozen caller in the stack,
    or None if the caller is not inside the project.
    """

    found_frozen: bool = False
    stack = inspect.stack()
    for frame in stack:
        # Direct attribute access: inspect.FrameInfo always has 'filename'
        filename = frame.filename
        if "frozen" in filename:
            found_frozen = True
            continue
        if found_frozen and "frozen" not in filename:
            try:
                return Path(filename).resolve().relative_to(PROJECT_ROOT)
            except ValueError:
                return None
    return None


@typechecked
def _is_caller_outside_project(caller: Path) -> bool:
    """
    Returns True if the importing module is outside the immich_autotag project root.
    """
    return not str(caller).startswith("immich_autotag")


@typechecked
def _is_caller_proxy_module_import(caller: Optional[Path]) -> bool:
    if caller is None:
        return False
    return "immich_autotag/api/immich_proxy" in str(caller)


@typechecked
def _is_immich_api_module(fullname: str) -> bool:
    return fullname.startswith("immich_client")


@typechecked
def _enforce_immich_api_import_rule(fullname: str, caller: Path) -> None:
    """
    Enforce the rule: Only the proxy module may import the Immich API.
    Raise ImportError if violated.
    """
    if _is_immich_api_module(fullname):
        if not _is_caller_proxy_module_import(caller):
            raise ImportError(
                f"Direct import of '{IMMICH_API_MODULE}' is forbidden. "
                "Only the proxy module may import it."
            )


@typechecked
def _enforce_immich_proxy_import_rule(fullname: str, caller: Path) -> None:
    """
    Enforce: Only logging_proxy can import any submodule from immich_proxy.
    Raise ImportError if violated.
    """
    # Block any import from immich_autotag.api.immich_proxy (including submodules)
    if fullname.startswith("immich_autotag.api.immich_proxy"):
        # Exception: allow in client_types.py as entry point to immich_client
        if str(caller).endswith("api/immich_proxy/client_types.py"):
            return None
        # Allow only if caller is inside logging_proxy

        if _is_caller_outside_logging_proxy(caller):
            raise ImportError(
                f"Direct import of '{fullname}' is forbidden outside {LOGGING_PROXY_MODULE}. "
                f"Only '{LOGGING_PROXY_MODULE}' may import from 'immich_autotag.api.immich_proxy'."
            )



        # ...other checks (example: forbidden modules)...
        return None  # Allow normal import to continue
# Nueva función auxiliar para comprobar si el caller está fuera de logging_proxy
@typechecked
def _is_caller_outside_logging_proxy(caller: Path) -> bool:
    """
    Returns True if the importing module is outside the logging_proxy module.
    """
    return LOGGING_PROXY_MODULE.replace(".", "/") not in str(caller)


@typechecked
def _enforce_logging_proxy_import_rule(fullname: str, caller: Path) -> None:
    """
    Enforce: No módulo de immich_proxy puede importar desde logging_proxy.
    Raise ImportError si se viola la regla.
    """
    if not _is_caller_proxy_module_import(caller):
        return
    logging_proxy_mod = logging_proxy.__name__
    if fullname.startswith(logging_proxy_mod):
        raise ImportError(
            f"Importación prohibida: '{fullname}' no puede ser importado desde '{caller}'.\n"
            f"Los módulos de immich_proxy no pueden importar desde {logging_proxy_mod} por restricción arquitectónica."
        )


class ArchitectureImportChecker:
    """
    Custom meta path finder for enforcing import architecture rules.
    """

    def find_spec(
        self,
        fullname: str,
        path: Optional[object] = None,
        target: Optional[object] = None,
    ) -> Optional[importlib.machinery.ModuleSpec]:
        # If the import is outside our project, skip restrictions
        if not ENABLE_ARCHITECTURE_IMPORT_HOOK:
            return None
        caller = _get_importing_module_relative_path()
        if caller is None:
            return None
        if _is_caller_outside_project(caller):
            return None

        _enforce_immich_api_import_rule(fullname, caller)
        _enforce_immich_proxy_import_rule(fullname, caller)
        _enforce_logging_proxy_import_rule(fullname, caller)
        return None


def install_architecture_import_hook():
    if not ENABLE_ARCHITECTURE_IMPORT_HOOK:
        return
    # Avoid double installation
    if not any(isinstance(f, ArchitectureImportChecker) for f in sys.meta_path):
        sys.meta_path.insert(0, ArchitectureImportChecker())


# --- App initialization pattern ---
def setup_import_architecture_hook():
    """
    Setup architecture import hook. Call this early in your app initialization,
    similar to logging/typeguard setup.
    """
    install_architecture_import_hook()


# Example usage: integrate in your main initialization
def initialize_app():
    # ...existing initialization code (logging, typeguard, etc.)...
    setup_import_architecture_hook()
    # ...other hooks or checks...


# For demonstration only: run as script
if __name__ == "__main__":
    initialize_app()
    print("math imported successfully")
