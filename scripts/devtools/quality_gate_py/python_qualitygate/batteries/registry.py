
from python_qualitygate.implementations.check_black import CheckBlack
from python_qualitygate.implementations.check_isort import CheckIsort
from python_qualitygate.implementations.check_python_syntax import CheckPythonSyntax
from python_qualitygate.implementations.check_ruff import CheckRuff
from python_qualitygate.implementations.check_flake8 import CheckFlake8
from python_qualitygate.implementations.check_mypy import CheckMypy
from python_qualitygate.implementations.check_shfmt import CheckShfmt
from scripts.devtools.quality_gate_py.python_qualitygate.implementations.spanish_check.check_no_spanish_chars import CheckNoSpanishChars
from python_qualitygate.implementations.check_jscpd import CheckJscpd
from python_qualitygate.implementations.check_no_tuples import CheckNoTuples
from python_qualitygate.implementations.check_import_linter import CheckImportLinter

from python_qualitygate.implementations.check_no_dynamic_attrs import CheckNoDynamicAttrs
from python_qualitygate.implementations.check_ssort import CheckSsort
from python_qualitygate.implementations.check_pylint_protected_access import CheckPylintProtectedAccess


# BATTERY_ORDER is now a list of check classes, defining the execution order statically and robustly
BATTERY_ORDER = [
    CheckPythonSyntax,
    CheckNoSpanishChars,
    CheckMypy,
    CheckJscpd,
    CheckImportLinter,
    CheckNoTuples,
    CheckShfmt,
    CheckIsort,
    CheckSsort,
    CheckBlack,
    CheckRuff,
    CheckFlake8,
    CheckPylintProtectedAccess,
    CheckNoDynamicAttrs,
]



# CHECKS map for lookup by name, using get_name() from an instance
from typing import Dict, Type
CHECKS: Dict[str, type] = {cls().get_name(): cls for cls in BATTERY_ORDER}

# No need for validation: BATTERY_ORDER is the single source of truth for order and membership
