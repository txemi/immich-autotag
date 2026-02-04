"""
rule_evaluator.py

Main entry point for evaluating all architecture import rules for a given import.
"""
from immich_autotag.architecture_import.immich_module_path import ImmichModulePath
from immich_autotag.architecture_import.module_path import ModulePath
from .rules import (
    enforce_immich_api_import_rule,
    enforce_immich_proxy_import_rule,
    enforce_logging_proxy_import_rule,
)

def evaluate_import_rules(imported_module: ModulePath, caller_info: ModulePath) -> None:
    """
    Evaluate all architecture import rules for a given import.
    Takes the imported module (as ImportedModuleInfo) and the caller (as CallerInfo).
    """
    my_caller_info : ImmichModulePath= ImmichModulePath.from_module_path(caller_info)
    my_caller_2=my_caller_info
    if  my_caller_2.is_outside_root_package():
        return None 
    imported2: ImmichModulePath=ImmichModulePath.from_module_path(imported_module) 
    enforce_immich_api_import_rule(imported2, my_caller_2)
    enforce_immich_proxy_import_rule(imported2, my_caller_2)
    enforce_logging_proxy_import_rule(imported2, my_caller_2)
    return None