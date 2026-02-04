"""
rule_evaluator.py

Main entry point for evaluating all architecture import rules for a given import.
"""
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
    enforce_immich_api_import_rule(imported_module, caller_info)
    enforce_immich_proxy_import_rule(imported_module, caller_info)
    enforce_logging_proxy_import_rule(imported_module, caller_info)
    return None