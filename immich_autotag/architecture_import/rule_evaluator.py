"""
rule_evaluator.py

Main entry point for evaluating all architecture import rules for a given import.
"""
from immich_autotag.architecture_import.immich_module_path import ImmichModulePath
from .fullname_info import ImportedModuleInfo
from .caller_info import CallerInfo
from .rules import (
    enforce_immich_api_import_rule,
    enforce_immich_proxy_import_rule,
    enforce_logging_proxy_import_rule,
)

def evaluate_import_rules(imported_module: ImportedModuleInfo, caller_info: CallerInfo) -> None:
    """
    Evaluate all architecture import rules for a given import.
    Takes the imported module (as ImportedModuleInfo) and the caller (as CallerInfo).
    """
    my_caller_info = caller_info.get_module_path()
    my_caller_2=ImmichModulePath(my_caller_info)
    if  my_caller_2.is_outside_project():
        return None
    imported=ImmichModulePath(imported_module.get_module_path())    
    enforce_immich_api_import_rule(imported, my_caller_2)
    enforce_immich_proxy_import_rule(imported, my_caller_2)
    enforce_logging_proxy_import_rule(imported, my_caller_2)
    return None