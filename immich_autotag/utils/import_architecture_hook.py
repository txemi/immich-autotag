"""
Import hook for architecture checks.
This module installs a custom import hook that checks every import against a set of architectural rules.
You can extend the logic to log, block, or warn about imports that violate your constraints.
"""

import importlib.abc
import importlib.util
import sys
from pathlib import Path

# Example: Block imports from forbidden packages

# No module except the proxy should import Immich API
IMMICH_API_MODULE = "immich_autotag.api.immich_proxy"


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def get_importing_module_relative_path():
    """
    Returns the relative path (to PROJECT_ROOT) of the first non-frozen caller in the stack,
    or None if the caller is not inside the project.
    """
    import inspect
    found_frozen = False
    stack = inspect.stack()
    for frame in stack:
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



def _is_outside_project() -> bool:
    """
    Returns True if the importing module is outside the immich_autotag project root.
    """
    rel = get_importing_module_relative_path()
    if rel is None or not str(rel).startswith("immich_autotag"):
        return True
    return False


def _is_proxy_module_import():
    rel = get_importing_module_relative_path()
    return rel is not None and "immich_autotag/api/immich_proxy" in str(rel)


def _is_immich_api_module(fullname: str) -> bool:
    return fullname.startswith("immich_client")


class ArchitectureImportChecker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # If the import is outside our project, skip restrictions
        if _is_outside_project():
            return None
        if _is_immich_api_module(fullname):
            if not _is_proxy_module_import():
                raise ImportError(
                    f"Direct import of '{IMMICH_API_MODULE}' is forbidden. Only the proxy module may import it."
                )

        # ...other checks (example: forbidden modules)...
        return None  # Allow normal import to continue


def install_architecture_import_hook():
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
    try:
        import os  # Should raise ImportError
    except ImportError as e:
        print(f"[ARCHITECTURE CHECK] {e}")

    print("math imported successfully")
