"""
Import hook for architecture checks.
This module installs a custom import hook that checks every import
against a set of architectural rules.
You can extend the logic to log, block, or warn about imports that
violate your constraints.
"""

import importlib.machinery
import inspect
import sys
from pathlib import Path
from typing import Optional

import attrs
from typeguard import typechecked

from immich_autotag.api import immich_proxy, logging_proxy
from immich_autotag.config.internal_config import ENABLE_ARCHITECTURE_IMPORT_HOOK

IMMICH_API_MODULE: str = immich_proxy.__name__
LOGGING_PROXY_MODULE: str = logging_proxy.__name__


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@attrs.define(frozen=True, auto_attribs=True)
class CallerInfo:

    _path: Path

    def is_outside_project(self) -> bool:
        return not str(self._path).startswith("immich_autotag")

    def is_proxy_module_import(self) -> bool:
        return (
            "immich_autotag/api/immich_proxy" in str(self._path)
        )

    def is_outside_logging_proxy(self) -> bool:
        return (
            LOGGING_PROXY_MODULE.replace(".", "/") not in str(self._path)
        )

    def is_client_types_entry(self) -> bool:
        return (
            str(self._path).endswith("api/immich_proxy/client_types.py")
        )

    @staticmethod
    @typechecked
    def from_stack() -> Optional["CallerInfo"]:
        """
        Returns a CallerInfo for the first non-frozen caller in the stack
        (relative to PROJECT_ROOT), or None if the caller is not inside the project.
        """
        found_frozen: bool = False
        stack = inspect.stack()
        for frame in stack:
            filename = frame.filename
            if "frozen" in filename:
                found_frozen = True
                continue
            if found_frozen and "frozen" not in filename:
                try:
                    rel_path = Path(filename).resolve().relative_to(PROJECT_ROOT)
                    return CallerInfo(rel_path)
                except ValueError:
                    return None
        return None

    def __str__(self):
        return str(self._path)


@attrs.define(frozen=True, auto_attribs=True)
class FullnameInfo:
    _fullname: str

    def is_immich_api_module(self) -> bool:
        return self._fullname.startswith("immich_client")

    def is_import_from_immich_proxy(self) -> bool:
        return self._fullname.startswith("immich_autotag.api.immich_proxy")

    def is_import_from_logging_proxy(self) -> bool:
        logging_proxy_mod = logging_proxy.__name__
        return self._fullname.startswith(logging_proxy_mod)

    def __str__(self):
        return self._fullname


@typechecked
def _enforce_immich_api_import_rule(fni: FullnameInfo, ci: CallerInfo) -> None:
    """
    Enforce the rule: Only the proxy module may import the Immich API.
    Raise ImportError if violated.
    """
    if fni.is_immich_api_module():
        if not ci.is_proxy_module_import():
            raise ImportError(
                f"Direct import of '{IMMICH_API_MODULE}' is forbidden. "
                "Only the proxy module may import it."
            )


def _enforce_immich_proxy_import_rule(fni: FullnameInfo, ci: CallerInfo) -> None:
    """
    Enforce: Only logging_proxy can import any submodule from immich_proxy.
    Raise ImportError if violated.
    """
    if fni.is_import_from_immich_proxy():
        if ci.is_client_types_entry():
            return None
        if ci.is_outside_logging_proxy():
            raise ImportError(
                f"Direct import of '{fni._fullname}' is forbidden outside "
                f"{LOGGING_PROXY_MODULE}. Only '{LOGGING_PROXY_MODULE}' may import from "
                f"'immich_autotag.api.immich_proxy'."
            )
        return None


def _enforce_logging_proxy_import_rule(fni: FullnameInfo, ci: CallerInfo) -> None:
    """
    Enforce: No immich_proxy module can import from logging_proxy.
    Raise ImportError if the rule is violated.
    """
    if not ci.is_proxy_module_import():
        return
    if fni.is_import_from_logging_proxy():
        logging_proxy_mod = logging_proxy.__name__
        raise ImportError(
            f"Forbidden import: '{fni._fullname}' cannot be imported from "
            f"'{ci._path}'.\n"
            f"immich_proxy modules are not allowed to import from "
            f"{logging_proxy_mod} due to architectural restriction."
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
        ci = CallerInfo.from_stack()
        if ci is None:
            return None
        if ci.is_outside_project():
            return None

        fni = FullnameInfo(fullname)
        _enforce_immich_api_import_rule(fni, ci)
        _enforce_immich_proxy_import_rule(fni, ci)
        _enforce_logging_proxy_import_rule(fni, ci)
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
