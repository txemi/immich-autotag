import inspect
from pathlib import Path
from typing import Optional

import attrs
from typeguard import typechecked

from immich_autotag.api import immich_proxy

from .shared_symbols import LOGGING_PROXY_MODULE_NAME

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


@attrs.define(frozen=True, auto_attribs=True)
class CallerInfo:
    _path: Path

    def is_outside_project(self) -> bool:
        # Use the root package name robustly
        return not str(self._path).startswith(self._get_root_package_path())

    @staticmethod
    def _get_root_package_path() -> str:
        """
        Returns the string path of the root package directory (e.g., 'immich_autotag')
        """
        root_name = __package__.split(".")[0]
        return str(Path(root_name))

    def is_proxy_module_import(self) -> bool:
        # Use the real path of the imported module, not a hardcoded string
        proxy_path = Path(immich_proxy.__file__).resolve().relative_to(PROJECT_ROOT)
        return str(proxy_path.parent) in str(self._path)

    def is_outside_logging_proxy(self) -> bool:
        return LOGGING_PROXY_MODULE_NAME.replace(".", "/") not in str(self._path)

    def is_client_types_entry(self) -> bool:
        return str(self._path).endswith("api/immich_proxy/client_types.py")

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
