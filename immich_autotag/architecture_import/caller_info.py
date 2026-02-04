"""
caller_info.py

Defines the CallerInfo class, which encapsulates information about the module performing an import
in the architecture rules system. It stores a ModulePath instance for semantic clarity, allowing
all queries and logic to be performed at the module/package level, not just file paths.
It is fundamental for applying dynamic architecture rules at runtime.
"""
import inspect
from pathlib import Path
from typing import Optional

import attrs
from typeguard import typechecked

from .immich_module_path import ImmichModulePath

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@attrs.define(frozen=True, auto_attribs=True)
class CallerInfo:

    def get_module_path(self) -> ImmichModulePath:
        """
        Returns the private _module_path attribute.
        """
        return self._module_path
    """
    Encapsulates information about the module performing an import.
    Stores an ImmichModulePath instance for semantic clarity, allowing all queries and logic
    to be performed at the module/package level, not just file paths.
    Used by the architecture rules system to apply dynamic restrictions at runtime.
    """
    _module_path: ImmichModulePath





    def is_outside_project(self) -> bool:
        # Delegate to ImmichModulePath logic
        return self._module_path.is_outside_root_package()

    def is_proxy_module_import(self) -> bool:
        return self._module_path.is_proxy_module_import()

    def is_outside_logging_proxy(self) -> bool:
        return self._module_path.is_outside_logging_proxy()

    def is_client_types_entry(self) -> bool:
        return self._module_path.is_client_types_entry()

    @staticmethod
    @typechecked
    def from_stack() -> Optional["CallerInfo"]:
        """
        Returns a CallerInfo for the first non-frozen caller in the stack
        (relative to PROJECT_ROOT), or None if the caller is not inside the project.
        """
        found_frozen: bool = False
        stack = inspect.stack()
        from .immich_module_path import ImmichModulePath
        for frame in stack:
            filename = frame.filename
            if "frozen" in filename:
                found_frozen = True
                continue
            if found_frozen and "frozen" not in filename:
                try:
                    rel_path = Path(filename).resolve().relative_to(PROJECT_ROOT)
                    # Convert rel_path to ImmichModulePath (dot notation)
                    immich_module_path = ImmichModulePath.from_path(rel_path)
                    return CallerInfo(immich_module_path)
                except ValueError:
                    return None
        return None

    def __str__(self):
        return self._module_path.as_dotstring()
