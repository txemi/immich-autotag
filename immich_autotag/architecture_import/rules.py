from immich_autotag.architecture_import.immich_module_path import ImmichModulePath
from immich_autotag.common import __name__ as COMMON_PKG_NAME


def enforce_common_package_import_rule(
    imported: ImmichModulePath, caller: ImmichModulePath
) -> None:
    """
    Enforce: The common package must not import anything from outside common.
    Raise ImportError if violated.
    """
    # Get the common package path
    common_path = ImmichModulePath.from_dotstring(COMMON_PKG_NAME)
    # If caller is in common but imported is not, raise
    if caller.is_submodule_of(common_path) and not imported.is_submodule_of(
        common_path
    ):
        raise ImportError(
            f"Forbidden import in 'common':\n"
            f"Importer: '{caller.as_dotstring()}'\n"
            f"Imported: '{imported.as_dotstring()}'\n"
            "The common package must not import anything from outside common."
        )


from .shared_symbols import (
    IMMICH_API_MODULE,
    LOGGING_PROXY_MODULE_NAME,
)


def enforce_immich_api_import_rule(
    imported: ImmichModulePath, caller: ImmichModulePath
) -> None:
    """
    Enforce the rule: Only the proxy module may import the Immich API.
    Raise ImportError if violated.
    """
    if imported.is_immich_api_module():
        if caller.is_architecture_rules():
            return None
        if not caller.is_proxy_module_import():
            raise ImportError(
                f"Direct import of '{IMMICH_API_MODULE}' is forbidden.\n"
                f"Importer: '{caller.as_dotstring()}'\n"
                f"Imported: '{imported.as_dotstring()}'\n"
                "Only the proxy module may import it."
            )


def enforce_immich_proxy_import_rule(
    imported: ImmichModulePath, caller: ImmichModulePath
) -> None:
    """
    Enforce: Only logging_proxy can import any submodule from immich_proxy.
    Raise ImportError if violated.
    """
    if imported.is_import_from_immich_proxy():
        if caller.is_import_from_immich_proxy():
            return None
        if caller.is_architecture_rules():
            return None
        if caller.is_outside_logging_proxy():
            caller.is_architecture_rules()
            raise ImportError(
                f"Direct import of '{str(imported)}' is forbidden outside "
                f"{LOGGING_PROXY_MODULE_NAME}.\n"
                f"Actual caller: '{str(caller)}'.\n"
                f"Only '{LOGGING_PROXY_MODULE_NAME}' may import from 'immich_autotag.api.immich_proxy'."
            )
        return None


def enforce_logging_proxy_import_rule(
    fni: ImmichModulePath, ci: ImmichModulePath
) -> None:
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
