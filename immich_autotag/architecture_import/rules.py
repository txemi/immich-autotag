from immich_autotag.architecture_import.immich_module_path import ImmichModulePath
from .caller_info import CallerInfo
from .shared_symbols import (
    IMMICH_API_MODULE,
    LOGGING_PROXY_MODULE_NAME,
)


def enforce_immich_api_import_rule(fni: ImmichModulePath, ci: ImmichModulePath) -> None:
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


def enforce_immich_proxy_import_rule(fni: ImmichModulePath, ci: ImmichModulePath) -> None:
    """
    Enforce: Only logging_proxy can import any submodule from immich_proxy.
    Raise ImportError if violated.
    """
    if fni.is_import_from_immich_proxy():
        if ci.is_client_types_entry():
            return None
        if ci.is_outside_logging_proxy():
            raise ImportError(
                f"Direct import of '{str(fni)}' is forbidden outside "
                f"{LOGGING_PROXY_MODULE_NAME}. Only '{LOGGING_PROXY_MODULE_NAME}' may import from "
                f"'immich_autotag.api.immich_proxy'."
            )
        return None


def enforce_logging_proxy_import_rule(fni: ImmichModulePath, ci: ImmichModulePath) -> None:
    """
    Enforce: No immich_proxy module can import from logging_proxy.
    Raise ImportError if the rule is violated.
    """
    if not ci.is_proxy_module_import():
        return
    if fni.is_import_from_logging_proxy():
        raise ImportError(
            f"Forbidden import: '{str(fni)}' cannot be imported from "
            f"'{str(ci)}'.\n"
            f"immich_proxy modules are not allowed to import from "
            f"{LOGGING_PROXY_MODULE_NAME} due to architectural restriction."
        )
