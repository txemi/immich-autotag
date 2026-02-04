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

from immich_autotag.api import immich_proxy

from .module_path import ModulePath
from .shared_symbols import LOGGING_PROXY_MODULE_NAME

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@attrs.define(frozen=True, auto_attribs=True)
class CallerInfo:
    """
    Encapsulates information about the module performing an import.
    Stores a ModulePath instance for semantic clarity, allowing all queries and logic
    to be performed at the module/package level, not just file paths.
    Used by the architecture rules system to apply dynamic restrictions at runtime.
    """
    module_path: ModulePath


    @staticmethod
    def _get_root_package_path() -> ModulePath:
        """
        Returns the root package as a ModulePath (e.g., ModulePath(('immich_autotag',)))
        """
        from .module_path import ModulePath
        name = Path(__file__).resolve().parent.name
        return ModulePath.from_dotstring(name)

    def is_outside_project(self) -> bool:
        # Use the root package ModulePath robustly
        root_path = self._get_root_package_path()
        return not self.module_path.parts or self.module_path.parts[0] != root_path.parts[0]

    def is_proxy_module_import(self) -> bool:
        # Example logic: check if the module path includes 'immich_proxy'
        return 'immich_proxy' in self.module_path.parts

    def is_outside_logging_proxy(self) -> bool:
        # Check if the module path includes the logging proxy module
        logging_proxy_parts = tuple(LOGGING_PROXY_MODULE_NAME.split('.'))
        return not all(part in self.module_path.parts for part in logging_proxy_parts)

    def is_client_types_entry(self) -> bool:
        # Example: check if the module path matches the client_types module
        return self.module_path.as_dotstring() == 'immich_autotag.api.immich_proxy.client_types'

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
                    # Convert rel_path to module path (dot notation)
                    module_path = ModulePath.from_path(rel_path)
                    return CallerInfo(module_path)
                except ValueError:
                    return None
        return None

    def __str__(self):
        return self.module_path.as_dotstring()
